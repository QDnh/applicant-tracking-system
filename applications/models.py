from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction

from candidates.models import Candidate
from jobs.models import JobOpening


class Application(models.Model):
    class Stage(models.TextChoices):
        APPLIED = "applied", "Applied"
        SCREENING = "screening", "Screening"
        INTERVIEW = "interview", "Interview"
        FINAL_REVIEW = "final_review", "Final Review"
        OFFER = "offer", "Offer"
        HIRED = "hired", "Hired"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    candidate = models.ForeignKey(Candidate, on_delete=models.PROTECT, related_name="applications")
    job_opening = models.ForeignKey(
        JobOpening, on_delete=models.PROTECT, related_name="applications"
    )
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.APPLIED)
    applied_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ACTIVE_STAGES = [
        Stage.APPLIED,
        Stage.SCREENING,
        Stage.INTERVIEW,
        Stage.FINAL_REVIEW,
        Stage.OFFER,
    ]
    # Rejected and Withdrawn free the pair for a new application; every other stage
    # (active stages and Hired) blocks it.
    NON_BLOCKING_STAGES = [Stage.REJECTED, Stage.WITHDRAWN]

    # The single source of truth for legal stage moves. Each stage lists its targets in
    # button order: the back move first (left), then the forward move (right), then the
    # final moves. A stage missing from the map (every final stage) has no moves.
    TRANSITIONS = {
        Stage.APPLIED: [Stage.SCREENING, Stage.REJECTED, Stage.WITHDRAWN],
        Stage.SCREENING: [Stage.APPLIED, Stage.INTERVIEW, Stage.REJECTED, Stage.WITHDRAWN],
        Stage.INTERVIEW: [Stage.SCREENING, Stage.FINAL_REVIEW, Stage.REJECTED, Stage.WITHDRAWN],
        Stage.FINAL_REVIEW: [Stage.INTERVIEW, Stage.OFFER, Stage.REJECTED, Stage.WITHDRAWN],
        Stage.OFFER: [Stage.FINAL_REVIEW, Stage.HIRED, Stage.REJECTED, Stage.WITHDRAWN],
    }

    class Meta:
        ordering = ["-applied_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "job_opening"],
                condition=~models.Q(stage__in=["rejected", "withdrawn"]),
                name="one_blocking_application_per_pair",
                violation_error_message=(
                    "This candidate already has an active or hired application for this job."
                ),
            ),
        ]

    def __str__(self):
        return f"{self.candidate} → {self.job_opening}"

    @property
    def is_active(self):
        return self.stage in self.ACTIVE_STAGES

    # Button labels for moves into final stages (other moves use the stage's own label).
    FINAL_MOVE_LABELS = {
        Stage.HIRED: "Hire",
        Stage.REJECTED: "Reject",
        Stage.WITHDRAWN: "Mark as withdrawn",
    }

    @property
    def moves(self):
        """Legal moves from the current stage, in button order, for templates to render.

        Each move has a direction: "back" (left slot), "forward" (right slot; Hire takes
        it at Offer) or "end" (Reject and Mark as withdrawn, after the other two).
        Moves into final stages can't be undone, so they carry a confirmation message.
        """
        position = self.ACTIVE_STAGES.index(self.stage) if self.is_active else None
        moves = []
        for target in self.TRANSITIONS.get(self.stage, []):
            final = target not in self.ACTIVE_STAGES
            if target == self.Stage.HIRED:
                direction = "forward"
            elif final:
                direction = "end"
            else:
                direction = "back" if self.ACTIVE_STAGES.index(target) < position else "forward"
            moves.append(
                {
                    "stage": target,
                    "label": self.FINAL_MOVE_LABELS.get(target, self.Stage(target).label),
                    "direction": direction,
                    "final": final,
                    "confirm": self.confirm_message(target) if final else None,
                }
            )
        return moves

    def confirm_message(self, to_stage):
        """The confirmation shown before a move into a final stage."""
        candidate, job = self.candidate, self.job_opening
        action = {
            self.Stage.HIRED: f"Hire {candidate} for {job}?",
            self.Stage.REJECTED: f"Reject {candidate}'s application for {job}?",
            self.Stage.WITHDRAWN: f"Mark {candidate}'s application for {job} as withdrawn?",
        }[to_stage]
        if to_stage == self.Stage.HIRED:
            titles = [
                str(other.job_opening) for other in self.other_active_applications().order_by("pk")
            ]
            if titles:
                count = len(titles)
                noun = "application" if count == 1 else "applications"
                action += (
                    f" This will also mark {candidate}'s {count} other active {noun} as "
                    f"withdrawn: {', '.join(titles)}."
                )
        return f"{action} This can't be undone."

    def other_active_applications(self):
        """The candidate's other active applications: the ones a hire here withdraws."""
        return (
            Application.objects.filter(candidate_id=self.candidate_id, stage__in=self.ACTIVE_STAGES)
            .exclude(pk=self.pk)
            .select_related("job_opening")
        )

    @classmethod
    def blocking(cls):
        """Applications that stop the same candidate applying to the same job again."""
        return cls.objects.exclude(stage__in=cls.NON_BLOCKING_STAGES)

    @classmethod
    def eligible_candidates(cls, job_opening):
        """Active candidates who could apply to this job now."""
        blocked = cls.blocking().filter(job_opening=job_opening).values("candidate")
        return Candidate.objects.filter(status=Candidate.Status.ACTIVE).exclude(pk__in=blocked)

    @classmethod
    def eligible_jobs(cls, candidate):
        """Open jobs this candidate could apply to now."""
        blocked = cls.blocking().filter(candidate=candidate).values("job_opening")
        return JobOpening.objects.filter(status=JobOpening.Status.OPEN).exclude(pk__in=blocked)

    @classmethod
    def record(cls, candidate, job_opening, user):
        """Create a new application in Applied, with its first stage-history row.

        The single entry point for new applications: checks eligibility here, with the
        conditional unique constraint as the final safeguard against simultaneous submits.
        """
        if job_opening.status != JobOpening.Status.OPEN:
            raise ValidationError(f"{job_opening} is closed and can't take new applications.")
        if candidate.status != Candidate.Status.ACTIVE:
            raise ValidationError(f"{candidate} isn't active and can't apply to jobs.")
        duplicate = ValidationError(
            f"{candidate} already has an active or hired application for {job_opening}."
        )
        if cls.blocking().filter(candidate=candidate, job_opening=job_opening).exists():
            raise duplicate

        try:
            with transaction.atomic():
                application = cls.objects.create(candidate=candidate, job_opening=job_opening)
                StageChange.objects.create(
                    application=application,
                    to_stage=cls.Stage.APPLIED,
                    changed_by=user,
                    changed_at=application.applied_at,
                )
        except IntegrityError as error:
            raise duplicate from error
        return application

    def move_to(self, to_stage, user):
        """The single entry point for every stage change.

        Validates against TRANSITIONS, then updates the stage and appends a StageChange
        row in one transaction. The stage is re-read under a row lock so the check uses
        the current stage, not whatever this instance was loaded with.
        """
        with transaction.atomic():
            from_stage = (
                Application.objects.select_for_update()
                .values_list("stage", flat=True)
                .get(pk=self.pk)
            )
            if to_stage not in self.TRANSITIONS.get(from_stage, []):
                labels = dict(self.Stage.choices)
                raise ValidationError(
                    f"Can't move from {labels[from_stage]} to {labels.get(to_stage, to_stage)}."
                )
            self.stage = to_stage
            self.save(update_fields=["stage", "updated_at"])
            StageChange.objects.create(
                application=self,
                from_stage=from_stage,
                to_stage=to_stage,
                changed_by=user,
                changed_at=self.updated_at,
            )
            if to_stage == self.Stage.HIRED:
                self._withdraw_other_active_applications(user, at=self.updated_at)

    def _withdraw_other_active_applications(self, user, at):
        """Hire side effect: the candidate's other active applications become Withdrawn.

        Runs inside the hire's transaction and stamps every row with the hire's time,
        so the hire and its withdrawals succeed or fail together and read as one event.
        Other candidates' applications to the same job are untouched.
        """
        others = self.other_active_applications().select_for_update()
        for other in others:
            StageChange.objects.create(
                application=other,
                from_stage=other.stage,
                to_stage=self.Stage.WITHDRAWN,
                changed_by=user,
                changed_at=at,
            )
        others.update(stage=self.Stage.WITHDRAWN, updated_at=at)


class StageChange(models.Model):
    """Append-only stage history: never edited, collapsed or deleted."""

    application = models.ForeignKey(
        Application, on_delete=models.PROTECT, related_name="stage_changes"
    )
    from_stage = models.CharField(max_length=20, choices=Application.Stage.choices, blank=True)
    to_stage = models.CharField(max_length=20, choices=Application.Stage.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stage_changes"
    )
    changed_at = models.DateTimeField()

    class Meta:
        ordering = ["-changed_at", "-pk"]

    def __str__(self):
        return f"{self.application}: {self.from_stage or '—'} → {self.to_stage}"
