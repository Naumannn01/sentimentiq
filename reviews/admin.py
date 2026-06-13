from django.contrib import admin
from .models import Source, Review, Sentiment, Aspect, WebhookSubscription, WebhookLog


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_url', 'is_active', 'created_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ['hotel_name', 'status', 'language', 'rating', 'reviewed_at', 'created_at']
    list_filter   = ['status', 'language', 'source']
    search_fields = ['hotel_name', 'body', 'reviewer']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Sentiment)
class SentimentAdmin(admin.ModelAdmin):
    list_display = ['review', 'label', 'model_used', 'confidence', 'created_at']
    list_filter  = ['label', 'model_used']


@admin.register(Aspect)
class AspectAdmin(admin.ModelAdmin):
    list_display = ['review', 'category', 'label', 'confidence']
    list_filter  = ['category', 'label']

@admin.register(WebhookSubscription)
class WebhookSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'target_url', 'hotel_name', 'event', 'is_active']
    list_filter  = ['event', 'is_active']

@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'review', 'result', 'status_code', 'fired_at']
    list_filter  = ['result']