import pytest
from rest_framework.test import APIClient
from reviews.models import Review, Source, Sentiment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def source(db):
    return Source.objects.create(name='TestSource')


@pytest.mark.django_db
class TestReviewSubmit:

    def test_submit_minimal_review(self, api_client):
        response = api_client.post('/api/v1/reviews/submit/', {
            'hotel_name': 'Test Hotel',
            'body': 'Great stay, loved it!',
            'language': 'en',
        })
        assert response.status_code == 201
        assert 'id' in response.data
        assert response.data['status'] == 'pending'

    def test_submit_missing_hotel_name_fails(self, api_client):
        response = api_client.post('/api/v1/reviews/submit/', {
            'body': 'Great stay!',
            'language': 'en',
        })
        assert response.status_code == 400
        assert 'hotel_name' in response.data


@pytest.mark.django_db
class TestBulkSubmit:

    def test_bulk_submit_valid(self, api_client):
        response = api_client.post('/api/v1/reviews/bulk/', {
            'reviews': [
                {'hotel_name': 'Hotel A', 'body': 'Nice place', 'language': 'en'},
                {'hotel_name': 'Hotel B', 'body': 'Average stay', 'language': 'en'},
            ]
        }, format='json')
        assert response.status_code == 201
        assert response.data['submitted'] == 2
        assert Review.objects.count() == 2

    def test_bulk_submit_exceeds_limit(self, api_client):
        reviews = [{'hotel_name': f'Hotel {i}', 'body': 'text', 'language': 'en'}
                   for i in range(501)]
        response = api_client.post('/api/v1/reviews/bulk/', {
            'reviews': reviews
        }, format='json')
        assert response.status_code == 400


@pytest.mark.django_db
class TestReviewRetrieval:

    def test_get_review_detail(self, api_client, source):
        review = Review.objects.create(
            source=source,
            hotel_name='Test Hotel',
            body='Amazing service',
            language='en',
            status='done',
        )
        Sentiment.objects.create(
            review=review,
            label='positive',
            model_used='roberta',
            confidence=0.95,
            pos_score=0.9,
            neu_score=0.05,
            neg_score=0.05,
        )

        response = api_client.get(f'/api/v1/reviews/{review.id}/')
        assert response.status_code == 200
        assert response.data['hotel_name'] == 'Test Hotel'
        assert response.data['sentiment']['label'] == 'positive'

    def test_list_reviews_with_label_filter(self, api_client, source):
        r1 = Review.objects.create(source=source, hotel_name='Hotel A',
                                    body='Loved it', language='en', status='done')
        r2 = Review.objects.create(source=source, hotel_name='Hotel A',
                                    body='Hated it', language='en', status='done')

        Sentiment.objects.create(review=r1, label='positive', model_used='roberta',
                                 confidence=0.9, pos_score=0.9, neu_score=0.05, neg_score=0.05)
        Sentiment.objects.create(review=r2, label='negative', model_used='roberta',
                                 confidence=0.9, pos_score=0.05, neu_score=0.05, neg_score=0.9)

        response = api_client.get('/api/v1/reviews/?label=positive')
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['sentiment']['label'] == 'positive'


@pytest.mark.django_db
class TestHotelStats:

    def test_hotel_stats_breakdown(self, api_client, source):
        r1 = Review.objects.create(source=source, hotel_name='Stats Hotel',
                                    body='Great', language='en', status='done')
        r2 = Review.objects.create(source=source, hotel_name='Stats Hotel',
                                    body='Bad', language='en', status='done')

        Sentiment.objects.create(review=r1, label='positive', model_used='roberta',
                                 confidence=0.9, pos_score=0.9, neu_score=0.05, neg_score=0.05)
        Sentiment.objects.create(review=r2, label='negative', model_used='roberta',
                                 confidence=0.9, pos_score=0.05, neu_score=0.05, neg_score=0.9)

        response = api_client.get('/api/v1/stats/Stats Hotel/')
        assert response.status_code == 200
        assert response.data['total_reviews'] == 2
        assert 'positive' in response.data['breakdown']
        assert 'negative' in response.data['breakdown']

    def test_hotel_stats_not_found(self, api_client):
        response = api_client.get('/api/v1/stats/Nonexistent Hotel/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestWebhooks:

    def test_register_webhook(self, api_client):
        response = api_client.post('/api/v1/webhooks/', {
            'name': 'Test Webhook',
            'target_url': 'https://example.com/hook',
            'hotel_name': '',
            'event': 'review.done',
        })
        assert response.status_code == 201
        assert response.data['is_active'] is True