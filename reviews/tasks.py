import requests
from celery import shared_task
from django.conf import settings
import hmac
import hashlib
import json
from .models import Review, Sentiment, Aspect, WebhookSubscription, WebhookLog




INFERENCE_URL = getattr(settings, 'INFERENCE_URL', 'http://localhost:8001') 
# Words but if someday the celery and signals does not communicate with other and fallback to localhost, you know where's the problem!


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_review(self, review_id: str):
    """
    Picks up a pending review, calls inference service,
    saves Sentiment + Aspect records, marks review as done.
    """
    try:
        # 1. Fetch review
        review = Review.objects.get(id=review_id)
        review.status = Review.Status.PROCESSING
        review.save(update_fields=['status'])

        # 2. Call inference service
        response = requests.post(
            f"{INFERENCE_URL}/predict",
            json={
                "review_id": str(review.id),
                "text": review.body,
                "language": review.language,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        # 3. Save overall sentiment
        Sentiment.objects.update_or_create(
            review=review,
            defaults={
                "label":       data["label"],
                "model_used":  data["model_used"],
                "confidence":  data["confidence"],
                "pos_score":   data["pos_score"],
                "neu_score":   data["neu_score"],
                "neg_score":   data["neg_score"],
                "shap_scores": data["shap_scores"],
            }
        )

        # 4. Save aspects
        for aspect in data["aspects"]:
            Aspect.objects.update_or_create(
                review=review,
                category=aspect["category"],
                defaults={
                    "label":      aspect["label"],
                    "confidence": aspect["confidence"],
                    "keywords":   aspect["keywords"],
                }
            )

        # 5. Mark done
        review.status = Review.Status.DONE
        review.save(update_fields=['status', 'updated_at'])

         # Fire webhooks async
        fire_webhooks.delay(str(review.id))

        return {"review_id": review_id, "label": data["label"]}

    except Review.DoesNotExist:
        return {"error": f"Review {review_id} not found"}

    except requests.RequestException as exc:
        # Retry on network errors
        review.status = Review.Status.PENDING
        review.save(update_fields=['status'])
        raise self.retry(exc=exc)

    except Exception as exc:
        review.status = Review.Status.FAILED
        review.save(update_fields=['status'])
        raise


@shared_task
def fire_webhooks(review_id: str):
    """Fires all matching webhook subscriptions for a completed review."""
    try:
        review = Review.objects.select_related('sentiment').get(id=review_id)
    except Review.DoesNotExist:
        return

    # Build payload
    payload = {
        'event':      'review.done',
        'review_id':  str(review.id),
        'hotel_name': review.hotel_name,
        'sentiment':  {
            'label':      review.sentiment.label,
            'confidence': review.sentiment.confidence,
        },
        'aspects': [
            {'category': a.category, 'label': a.label}
            for a in review.aspects.all()
        ],
    }
    payload_bytes = json.dumps(payload).encode('utf-8')

    # Find matching subscriptions
    subscriptions = WebhookSubscription.objects.filter(
        is_active=True,
        event=WebhookSubscription.Event.REVIEW_DONE,
    ).filter(
        # either subscribed to all hotels or specifically this one
        hotel_name__in=['', review.hotel_name]
    )

    for sub in subscriptions:
        _fire_single(sub, review, payload, payload_bytes)


def _fire_single(sub, review, payload, payload_bytes):
    """Fires one webhook and logs the result."""
    headers = {'Content-Type': 'application/json'}

    # HMAC signature if secret is set
    if sub.secret:
        sig = hmac.new(
            sub.secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        headers['X-SentimentIQ-Signature'] = f"sha256={sig}"

    result = WebhookLog.Result.FAILED
    status_code = None
    response_text = ''

    try:
        resp = requests.post(
            sub.target_url,
            data=payload_bytes,
            headers=headers,
            timeout=10,
        )
        status_code = resp.status_code
        response_text = resp.text[:500]
        result = WebhookLog.Result.SUCCESS if resp.ok else WebhookLog.Result.FAILED

    except requests.RequestException as e:
        response_text = str(e)

    WebhookLog.objects.create(
        subscription=sub,
        review=review,
        result=result,
        status_code=status_code,
        response=response_text,
    )