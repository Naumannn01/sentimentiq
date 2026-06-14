from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
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


class BulkReviewSubmitView(APIView):
    """POST /api/v1/reviews/bulk/ — up to 500 manual submissions."""

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

        return Response({
            'hotel_name': hotel_name,
            'total_reviews': total,
            'breakdown': {
                b['sentiment__label']: {
                    'count': b['count'],
                    'percentage': round(b['count'] / total * 100, 1)
                }
                for b in breakdown
            }
        })


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