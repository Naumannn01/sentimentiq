from rest_framework import serializers
from .models import Review, Sentiment, Aspect, Source, WebhookSubscription, WebhookLog


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ['id', 'name', 'base_url']


class AspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aspect
        fields = ['category', 'label', 'confidence', 'keywords']


class SentimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sentiment
        fields = ['label', 'model_used', 'confidence',
                  'pos_score', 'neu_score', 'neg_score', 'shap_scores']


class ManualReviewSerializer(serializers.ModelSerializer):
    """For direct API submissions — no source or external_id needed."""
    reviewer    = serializers.CharField(required=False, allow_blank=True, default='')
    rating      = serializers.DecimalField(required=False, allow_null=True,
                                           max_digits=3, decimal_places=1)
    reviewed_at = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model  = Review
        fields = ['hotel_name', 'body', 'rating', 'language', 'reviewer', 'reviewed_at']


class PlatformReviewSerializer(serializers.ModelSerializer):
    """For imports from TripAdvisor, Booking.com etc — source + external_id required."""
    class Meta:
        model  = Review
        fields = ['hotel_name', 'body', 'rating', 'language',
                  'reviewer', 'source', 'external_id', 'reviewed_at']


class BulkReviewSerializer(serializers.Serializer):
    """Bulk manual submissions."""
    reviews = ManualReviewSerializer(many=True)

    def validate_reviews(self, value):
        if len(value) > 500:
            raise serializers.ValidationError("Max 500 reviews per batch.")
        return value


class ReviewResultSerializer(serializers.ModelSerializer):
    """Used for GET — reading results with nested sentiment + aspects."""
    sentiment = SentimentSerializer(read_only=True)
    aspects   = AspectSerializer(many=True, read_only=True)
    source    = SourceSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'hotel_name', 'reviewer', 'body', 'rating',
                  'language', 'status', 'reviewed_at', 'created_at',
                  'source', 'sentiment', 'aspects']
        


class WebhookSubscriptionSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model  = WebhookSubscription
        fields = ['id', 'name', 'target_url', 'hotel_name', 'event',
                  'secret', 'is_active', 'created_at']
        extra_kwargs = {'secret': {'write_only': True}}


class WebhookLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WebhookLog
        fields = ['id', 'result', 'status_code', 'response', 'fired_at']