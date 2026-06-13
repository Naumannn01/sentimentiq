import uuid
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class Source(models.Model):
    """Where the review came from — TripAdvisor, Booking.com, manual upload, etc."""

    name = models.CharField(max_length=100, unique=True)
    base_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Review(models.Model):

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        PROCESSING = 'processing', 'Processing'
        DONE      = 'done',      'Done'
        FAILED    = 'failed',    'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='reviews')

    external_id  = models.CharField(max_length=255, blank=True)   # ID on the source platform
    hotel_name   = models.CharField(max_length=255)
    reviewer     = models.CharField(max_length=255, blank=True)
    body         = models.TextField()
    rating       = models.DecimalField(max_digits=3, decimal_places=1,
                                       null=True, blank=True)      # e.g. 4.5 / 5
    language     = models.CharField(max_length=10, default='en')
    status       = models.CharField(max_length=20, choices=Status.choices,
                                    default=Status.PENDING, db_index=True)
    reviewed_at  = models.DateTimeField(null=True, blank=True)     # original review date
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hotel_name', 'status']),
            models.Index(fields=['reviewed_at']),
        ]
        constraints = [
        models.UniqueConstraint(
            fields=['source', 'external_id'],
            condition=models.Q(source__isnull=False) & ~models.Q(external_id=''),
            name='unique_review_per_source'
        )
    ]

    def __str__(self):
        return f"{self.hotel_name} — {self.id}"


class Sentiment(models.Model):

    class Label(models.TextChoices):
        POSITIVE = 'positive', 'Positive'
        NEUTRAL  = 'neutral',  'Neutral'
        NEGATIVE = 'negative', 'Negative'

    class Model(models.TextChoices):
        ROBERTA = 'roberta', 'RoBERTa'
        VADER   = 'vader',   'VADER'

    review     = models.OneToOneField(Review, on_delete=models.CASCADE,
                                      related_name='sentiment')
    label      = models.CharField(max_length=20, choices=Label.choices, db_index=True)
    model_used = models.CharField(max_length=20, choices=Model.choices)
    confidence = models.FloatField()                # 0.0 – 1.0
    pos_score  = models.FloatField(default=0)
    neu_score  = models.FloatField(default=0)
    neg_score  = models.FloatField(default=0)
    shap_scores = models.JSONField(default=dict, blank=True)  # token → weight
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.review_id} → {self.label} ({self.confidence:.0%})"


class Aspect(models.Model):
    """Per-aspect sentiment — room, staff, food, value, cleanliness, location."""

    class Category(models.TextChoices):
        ROOM        = 'room',        'Room'
        STAFF       = 'staff',       'Staff'
        FOOD        = 'food',        'Food'
        VALUE       = 'value',       'Value'
        CLEANLINESS = 'cleanliness', 'Cleanliness'
        LOCATION    = 'location',    'Location'
        OTHER       = 'other',       'Other'

    class Label(models.TextChoices):
        POSITIVE = 'positive', 'Positive'
        NEUTRAL  = 'neutral',  'Neutral'
        NEGATIVE = 'negative', 'Negative'

    review     = models.ForeignKey(Review, on_delete=models.CASCADE,
                                   related_name='aspects')
    category   = models.CharField(max_length=20, choices=Category.choices, db_index=True)
    label      = models.CharField(max_length=20, choices=Label.choices)
    confidence = models.FloatField()
    keywords   = models.JSONField(default=list)    # ["dirty", "smelled", "stained"]
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('review', 'category')]

    def __str__(self):
        return f"{self.review_id} | {self.category}: {self.label}"



@receiver(post_save, sender=Review)
def queue_review_on_create(sender, instance, created, **kwargs):
    if created and instance.status == Review.Status.PENDING:
        # import here to avoid circular imports
        from .tasks import process_review
        process_review.delay(str(instance.id))


class WebhookSubscription(models.Model):

    class Event(models.TextChoices):
        REVIEW_DONE     = 'review.done',     'Review Done'
        SENTIMENT_DROP  = 'sentiment.drop',  'Sentiment Drop'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=100)         # e.g. "Hyatt PMS"
    target_url  = models.URLField()                        # where we POST to
    hotel_name  = models.CharField(max_length=255,
                                   blank=True)             # filter by hotel, empty = all
    event       = models.CharField(max_length=30,
                                   choices=Event.choices,
                                   default=Event.REVIEW_DONE)
    secret      = models.CharField(max_length=255,
                                   blank=True)             # for HMAC signing
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} → {self.target_url}"


class WebhookLog(models.Model):
    """Tracks every outgoing webhook attempt."""

    class Result(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILED  = 'failed',  'Failed'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(WebhookSubscription, on_delete=models.CASCADE,
                                     related_name='logs')
    review       = models.ForeignKey(Review, on_delete=models.CASCADE,
                                     related_name='webhook_logs')
    result       = models.CharField(max_length=20, choices=Result.choices)
    status_code  = models.IntegerField(null=True, blank=True)
    response     = models.TextField(blank=True)
    fired_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subscription.name} — {self.result} ({self.fired_at})"