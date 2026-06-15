from django.urls import path
from . import views

urlpatterns = [
    path('reviews/',            views.ReviewListView.as_view(),         name='review-list'),
    path('reviews/submit/',     views.ReviewSubmitView.as_view(),       name='review-submit'),
    path('reviews/bulk/',       views.BulkReviewSubmitView.as_view(),   name='review-bulk'),
    path('stats/<str:hotel_name>/trend/', views.HotelTrendView.as_view(), name='hotel-trend'),
    path('stats/<str:hotel_name>/', views.HotelStatsView.as_view(), name='hotel-stats'),
    path('reviews/<uuid:id>/',  views.ReviewResultView.as_view(),       name='review-detail'),
    path('stats/<str:hotel_name>/', views.HotelStatsView.as_view(),    name='hotel-stats'),
    path('sources/',            views.SourceListView.as_view(),         name='source-list'),
    path('webhooks/',           views.WebhookSubscriptionView.as_view(), name='webhook-list'),
    path('webhooks/<uuid:id>/', views.WebhookDetailView.as_view(),      name='webhook-detail'),
    path('webhooks/<uuid:id>/logs/', views.WebhookLogView.as_view(),    name='webhook-logs'),
    path('hotels/', views.HotelListView.as_view(), name='hotel-list'),
]