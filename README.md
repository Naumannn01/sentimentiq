# SentimentIQ — Hotel Review Sentiment Analysis Pipeline

An end-to-end NLP system that ingests hotel reviews, classifies sentiment using a fine-tuned transformer model with a rule-based fallback, breaks results down by aspect (room, staff, food, etc.), and surfaces everything through a REST API, real-time webhooks, and an interactive dashboard.

Built to demonstrate a production-style architecture: async processing, model fallback strategy, explainability, and a fully tested, CI-backed codebase — not just a notebook.

---

## Architecture

```
                    ┌─────────────┐
   Client / API ──▶│   Django     │──▶ PostgreSQL (reviews, sentiment, aspects)
   (submit review)  │   + DRF      │
                    └──────┬───────┘
                           │ signal
                           ▼
                    ┌─────────────┐
                    │   Celery     │◀── Redis (broker + result backend)
                    │   Worker     │
                    └──────┬───────┘
                           │ HTTP
                           ▼
                    ┌─────────────┐
                    │  FastAPI     │
                    │  Inference   │  RoBERTa (primary) + VADER (fallback)
                    │  Service     │  Aspect detection · token-level scoring
                    └─────────────┘

                    ┌─────────────┐
                    │   React      │──▶ Recharts dashboard, hotel browser,
                    │  Dashboard   │    live review submission
                    └─────────────┘

   Webhooks ──▶ Subscribers get pushed sentiment results on review completion
```

---

## Tech Stack

| Layer            | Technology                                      |
|------------------|--------------------------------------------------|
| Backend          | Django, Django REST Framework                   |
| Async processing | Celery, Redis                                   |
| Database         | PostgreSQL                                      |
| ML / NLP         | Hugging Face Transformers (RoBERTa), VADER      |
| Inference API    | FastAPI                                         |
| Frontend         | React, Vite, Recharts, Axios                    |
| Testing          | pytest, pytest-django                           |
| CI/CD            | GitHub Actions                                  |
| Containerization | Docker, Docker Compose                          |

---

## Features

- **Dual-model sentiment classification** — RoBERTa (`cardiffnlp/twitter-roberta-base-sentiment-latest`) runs first; if confidence drops below 60%, VADER acts as a rule-based fallback.
- **Aspect-based sentiment** — every review is scanned for six categories (room, staff, food, value, cleanliness, location) and scored independently.
- **Token-level explainability** — per-token sentiment contribution scores stored alongside each prediction.
- **Async pipeline** — review submission triggers a Celery task via Django signals; processing happens off the request/response cycle.
- **Versioned REST API** — submit single or bulk reviews, retrieve results, filter by sentiment/hotel, get per-hotel sentiment breakdowns.
- **Webhooks** — subscribers receive a POST with the full sentiment payload (label, confidence, aspects) the moment a review finishes processing, with HMAC signing support and delivery logs.
- **React dashboard** — browse all hotels, view sentiment distribution and aspect breakdowns as charts, submit a new review and watch it get classified live.
- **Automated tests + CI** — pytest suite covering all endpoints, run automatically on every push via GitHub Actions.
- **Benchmark script** — compares RoBERTa vs VADER accuracy on a labeled sample, output to `benchmark_results.json`.

---

## Project Structure

```
sentimentiq/
├── config/                  # Django project settings, Celery config
│   └── settings/
│       ├── base.py
│       └── local.py
├── reviews/                  # Main Django app
│   ├── models.py             # Review, Sentiment, Aspect, Source, Webhook models
│   ├── serializers.py         # Manual vs platform review serializers
│   ├── views.py               # API views
│   ├── tasks.py               # Celery tasks (processing + webhooks)
│   ├── urls.py
│   └── tests/
│       └── test_api.py
├── inference/                 # Standalone FastAPI inference service
│   ├── main.py
│   ├── predictor.py            # RoBERTa + VADER + aspect logic
│   ├── schemas.py
│   ├── benchmark.py
│   └── requirements.txt
├── dashboard/                  # React + Vite frontend
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── components/
├── .github/workflows/ci.yml    # GitHub Actions pipeline
├── docker-compose.yml
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js (for the dashboard)

### Backend setup

```bash
git clone https://github.com/Naumannn01/sentimentiq.git
cd sentimentiq
cp .env.example .env   # fill in your own values

docker compose up --build
```

This starts five services: `db` (PostgreSQL), `redis`, `web` (Django), `worker` (Celery), and `inference` (FastAPI + RoBERTa). First boot downloads the RoBERTa model weights (~250MB) — subsequent boots use the cached model.

Run migrations:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

### Frontend setup

```bash
cd dashboard
npm install
npm run dev
```

Visit `http://localhost:5173`. Make sure the backend stack (`docker compose ps`) shows all 5 containers running first — otherwise submitted reviews stay `pending`.

---

## API Reference

Base URL: `http://localhost:8000/api/v1/`

| Method | Endpoint                          | Description                                  |
|--------|-----------------------------------|-----------------------------------------------|
| POST   | `/reviews/submit/`                | Submit a single review                       |
| POST   | `/reviews/bulk/`                  | Submit up to 500 reviews at once             |
| GET    | `/reviews/`                       | List reviews (filter by `label`, `hotel_name`, `status`, `language`) |
| GET    | `/reviews/<id>/`                  | Get a single review with sentiment + aspects |
| GET    | `/hotels/`                        | List all hotels with review counts           |
| GET    | `/stats/<hotel_name>/`            | Sentiment breakdown for a hotel              |
| GET    | `/sources/`                       | List review sources                          |
| POST   | `/webhooks/`                      | Register a webhook subscription              |
| GET    | `/webhooks/<id>/logs/`            | View webhook delivery history                |

### Example — submit a review

```bash
curl -X POST http://localhost:8000/api/v1/reviews/submit/ \
  -H "Content-Type: application/json" \
  -d '{
    "hotel_name": "Taj Mumbai",
    "body": "Fantastic stay, room was spotless and staff incredibly friendly.",
    "language": "en"
  }'
```

Response:

```json
{
  "id": "94f42a8a-b279-43cc-9812-61962bdcdc20",
  "status": "pending"
}
```

Poll `/reviews/<id>/` until `status` is `done` to retrieve the sentiment, confidence, and aspect breakdown.

---

## How Sentiment Classification Works

1. Text is sent to RoBERTa, which returns probabilities across negative / neutral / positive.
2. If RoBERTa's top confidence is **below 60%**, VADER (rule-based) re-scores the text and its result is used instead — RoBERTa can be uncertain on short, sarcastic, or ambiguous reviews where a lexicon-based approach is more stable.
3. The text is scanned against keyword sets for six aspect categories. For each matched category, the relevant sentences are extracted and scored independently with VADER.
4. Token-level sentiment contributions are computed and stored for explainability.

---

## Benchmark Results

Run the benchmark yourself:

```bash
docker compose exec inference python benchmark.py
```

This scores both models against a hand-labeled set of reviews and writes `benchmark_results.json` with per-model accuracy and a full breakdown of predictions vs ground truth.

---

## Testing

```bash
docker compose exec web pytest
```

Test suite covers: review submission (single + bulk), validation errors, result retrieval, sentiment filtering, hotel stats, and webhook registration.

CI runs this automatically on every push to `main` via GitHub Actions (`.github/workflows/ci.yml`), spinning up Postgres and Redis as service containers.

---

## Webhooks

Register a subscriber to receive a POST request whenever a review finishes processing:

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My PMS Integration",
    "target_url": "https://example.com/webhook",
    "hotel_name": "",
    "event": "review.done",
    "is_active": true
  }'
```

Payload sent on completion:

```json
{
  "event": "review.done",
  "review_id": "...",
  "hotel_name": "Taj Mumbai",
  "sentiment": { "label": "positive", "confidence": 0.94 },
  "aspects": [
    { "category": "staff", "label": "positive" },
    { "category": "cleanliness", "label": "positive" }
  ]
}
```

If a `secret` is set on the subscription, requests are signed with `X-SentimentIQ-Signature: sha256=<hmac>`.

---

## Design Decisions

- **Separate inference service** — keeps the ML runtime decoupled from the web layer, so the model can be swapped, scaled, or redeployed independently of Django.
- **Confidence-based fallback** — rather than relying on a single model, low-confidence RoBERTa predictions defer to VADER, reducing the risk of confidently-wrong classifications on edge cases.
- **Conditional unique constraint** — `Review` enforces source/external_id uniqueness only when both are present, allowing both platform imports (deduplicated) and direct manual submissions (no source needed) through separate serializers.
- **Lightweight explainability** — token-level scores use a VADER-based proxy rather than full SHAP, keeping the inference container lean while still surfacing which words drove a prediction.

---

## Roadmap / Possible Extensions

- Fine-tune RoBERTa on a hospitality-specific corpus for higher accuracy
- Multilingual support via language detection + multilingual model routing
- Expand the benchmark set for statistically meaningful accuracy comparisons
- Dedicated MLflow or experiment-tracking service for model versioning
- Sentiment trend-over-time charts on the dashboard

---

## License

MIT