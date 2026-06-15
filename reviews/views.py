from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from django.db import connection
from django.core.cache import cache
from django.http import JsonResponse
from django.views import View
import hashlib
from rest_framework.throttling import AnonRateThrottle
from django.db.models.functions import TruncDate
from .models import Review, Source, WebhookSubscription, WebhookLog
from .serializers import (
    ManualReviewSerializer, PlatformReviewSerializer,
    ReviewResultSerializer, BulkReviewSerializer,
    SourceSerializer, WebhookSubscriptionSerializer, WebhookLogSerializer
)


class ReviewSubmitView(generics.CreateAPIView):
    """POST /api/v1/reviews/submit/ — single manual submission."""
    serializer_class = ManualReviewSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(status='pending')
        return Response(
            {'id': str(review.id), 'status': review.status},
            status=status.HTTP_201_CREATED
        )
    
class BulkSubmitThrottle(AnonRateThrottle):
    scope = 'bulk_submit'

class BulkReviewSubmitView(APIView):
    """POST /api/v1/reviews/bulk/ — up to 500 manual submissions."""
    throttle_classes = [BulkSubmitThrottle]

    def post(self, request):
        serializer = BulkReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reviews_data = serializer.validated_data['reviews']
        created = []
        for data in reviews_data:
            review = Review.objects.create(**data, status='pending')
            created.append({'id': str(review.id), 'status': review.status})

        return Response(
            {'submitted': len(created), 'reviews': created},
            status=status.HTTP_201_CREATED
        )

class ReviewResultView(generics.RetrieveAPIView):
    """GET /api/v1/reviews/<id>/ — get result for a single review."""
    serializer_class = ReviewResultSerializer
    queryset = Review.objects.prefetch_related('aspects').select_related('sentiment', 'source')
    lookup_field = 'id'


class ReviewListView(generics.ListAPIView):
    """GET /api/v1/reviews/ — list reviews with filters."""
    serializer_class = ReviewResultSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'language', 'hotel_name']
    ordering_fields  = ['created_at', 'rating']
    ordering         = ['-created_at']

    def get_queryset(self):
        qs = Review.objects.prefetch_related('aspects').select_related('sentiment', 'source')

        # optional filters via query params
        label = self.request.query_params.get('label')
        hotel = self.request.query_params.get('hotel_name')
        if label:
            qs = qs.filter(sentiment__label=label)
        if hotel:
            qs = qs.filter(hotel_name__icontains=hotel)
        return qs


class BulkReviewSubmitView(APIView):
    """POST /api/v1/reviews/bulk/ — submit up to 500 reviews at once."""

    def post(self, request):
        serializer = BulkReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reviews_data = serializer.validated_data['reviews']
        created = []
        for data in reviews_data:
            review = Review.objects.create(**data, status='pending')
            created.append({'id': str(review.id), 'status': review.status})

        return Response(
            {'submitted': len(created), 'reviews': created},
            status=status.HTTP_201_CREATED
        )


class HotelStatsView(APIView):
    """GET /api/v1/stats/<hotel_name>/ — sentiment breakdown for a hotel."""

    def get(self, request, hotel_name):
        cache_key = f"hotel_stats:{hashlib.md5(hotel_name.lower().encode()).hexdigest()}"
        # cache_key = f"hotel_stats:{hotel_name.lower()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        reviews = Review.objects.filter(
            hotel_name__iexact=hotel_name,
            status='done'
        ).select_related('sentiment')

        if not reviews.exists():
            return Response({'error': 'No reviews found.'}, status=404)

        total = reviews.count()
        breakdown = (
            reviews.values('sentiment__label')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        result = {
            'hotel_name': hotel_name,
            'total_reviews': total,
            'breakdown': {
                b['sentiment__label']: {
                    'count': b['count'],
                    'percentage': round(b['count'] / total * 100, 1)
                }
                for b in breakdown
            }
        }

        cache.set(cache_key, result, timeout=120)  # 2 minutes
        return Response(result)

class SourceListView(generics.ListCreateAPIView):
    """GET/POST /api/v1/sources/"""
    serializer_class = SourceSerializer
    queryset = Source.objects.filter(is_active=True)





class WebhookSubscriptionView(generics.ListCreateAPIView):
    serializer_class = WebhookSubscriptionSerializer
    queryset = WebhookSubscription.objects.filter(is_active=True).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(is_active=True)

class WebhookDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/webhooks/<id>/"""
    serializer_class = WebhookSubscriptionSerializer
    queryset = WebhookSubscription.objects.all()
    lookup_field = 'id'


class WebhookLogView(generics.ListAPIView):
    """GET /api/v1/webhooks/<id>/logs/ — delivery history for a subscription."""
    serializer_class = WebhookLogSerializer

    def get_queryset(self):
        return WebhookLog.objects.filter(
            subscription_id=self.kwargs['id']
        ).order_by('-fired_at')
    

class HotelListView(APIView):
    """GET /api/v1/hotels/ — list all hotels with review counts."""

    def get(self, request):
        hotels = (
            Review.objects.filter(status='done')
            .values('hotel_name')
            .annotate(review_count=Count('id'))
            .order_by('-review_count')
        )
        return Response(list(hotels))
    
class WebhookSubscriptionView(generics.ListCreateAPIView):
    """GET/POST /api/v1/webhooks/ — list or register a webhook."""
    serializer_class = WebhookSubscriptionSerializer
    queryset = WebhookSubscription.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(is_active=True)

class HealthCheckView(View):
    def get(self, request):
        status = {"status": "ok", "checks": {}}
        http_status = 200

        try:
            connection.ensure_connection()
            status["checks"]["database"] = "ok"
        except Exception as e:
            status["checks"]["database"] = f"error: {e}"
            status["status"] = "error"
            http_status = 503

        try:
            cache.set("health_check", "ok", 5)
            if cache.get("health_check") == "ok":
                status["checks"]["redis"] = "ok"
            else:
                raise Exception("cache mismatch")
        except Exception as e:
            status["checks"]["redis"] = f"error: {e}"
            status["status"] = "error"
            http_status = 503

        return JsonResponse(status, status=http_status)
    

class HotelTrendView(APIView):
    """GET /api/v1/stats/<hotel_name>/trend/ — daily sentiment counts."""

    def get(self, request, hotel_name):
        reviews = Review.objects.filter(
            hotel_name__iexact=hotel_name,
            status='done'
        ).select_related('sentiment')

        if not reviews.exists():
            return Response({'error': 'No reviews found.'}, status=404)

        trend = (
            reviews
            .annotate(date=TruncDate('created_at'))
            .values('date', 'sentiment__label')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        data = {}
        for row in trend:
            date_str = row['date'].isoformat()
            if date_str not in data:
                data[date_str] = {'date': date_str, 'positive': 0, 'neutral': 0, 'negative': 0}
            label = row['sentiment__label']
            if label in data[date_str]:
                data[date_str][label] = row['count']

        return Response(sorted(data.values(), key=lambda x: x['date']))
