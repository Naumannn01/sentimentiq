import re
# import shap
import numpy as np
from transformers import AutoTokenizer, pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from schemas import ReviewRequest, PredictionResponse, AspectResult

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

ASPECT_KEYWORDS = {
    'room':        ['room', 'bed', 'bathroom', 'shower', 'view', 'noise', 'space', 'suite'],
    'staff':       ['staff', 'service', 'reception', 'helpful', 'friendly', 'rude', 'ignored'],
    'food':        ['food', 'breakfast', 'restaurant', 'dinner', 'meal', 'buffet', 'taste'],
    'value':       ['price', 'value', 'expensive', 'cheap', 'worth', 'overpriced', 'deal'],
    'cleanliness': ['clean', 'dirty', 'smell', 'stain', 'hygiene', 'spotless', 'dusty'],
    'location':    ['location', 'central', 'transport', 'airport', 'walk', 'nearby', 'area'],
}

LABEL_MAP = {
    'LABEL_0': 'negative',
    'LABEL_1': 'neutral',
    'LABEL_2': 'positive',
}


class Predictor:

    def __init__(self):
        self.ready = False
        self.model_name = 'roberta'
        self.tokenizer = None
        self.model = None
        self.vader = None
        self.explainer = None

    def load(self):
        print("[predictor] loading RoBERTa via pipeline...")
        self.pipe = pipeline(
            "text-classification",
            model=MODEL_NAME,
            tokenizer=MODEL_NAME,
            top_k=None,         # return all 3 label scores
            truncation=True,
            max_length=512,
        )

        print("[predictor] loading VADER...")
        self.vader = SentimentIntensityAnalyzer()


        self.ready = True
        print("[predictor] all models ready.")

    # ------------------------------------------------------------------ #
    #  RoBERTa                                                             #
    # ------------------------------------------------------------------ #

    def _roberta_predict_proba(self, texts):
        """Returns (N, 3) numpy array — [neg, neu, pos]."""
        results = self.pipe(list(texts))
        out = []
        for result in results:
            scores = {r['label']: r['score'] for r in result}
            out.append([
                scores.get('negative', 0),
                scores.get('neutral', 0),
                scores.get('positive', 0),
            ])
        return np.array(out)

    def _roberta_sentiment(self, text: str) -> tuple:
        """Returns (label, confidence, neg, neu, pos)."""
        probs = self._roberta_predict_proba([text])[0]
        neg, neu, pos = float(probs[0]), float(probs[1]), float(probs[2])
        idx = int(np.argmax(probs))
        label = LABEL_MAP[f'LABEL_{idx}']
        confidence = round(float(probs[idx]), 4)
        return label, confidence, round(pos, 4), round(neu, 4), round(neg, 4)

    # ------------------------------------------------------------------ #
    #  VADER fallback — used when confidence is low                        #
    # ------------------------------------------------------------------ #

    def _vader_sentiment(self, text: str) -> tuple:
        scores = self.vader.polarity_scores(text)
        compound = scores['compound']
        if compound >= 0.05:
            label, confidence = 'positive', round(0.5 + compound / 2, 4)
        elif compound <= -0.05:
            label, confidence = 'negative', round(0.5 + abs(compound) / 2, 4)
        else:
            label, confidence = 'neutral', round(1 - abs(compound), 4)
        return label, confidence, \
               round(scores['pos'], 4), round(scores['neu'], 4), round(scores['neg'], 4)

    # ------------------------------------------------------------------ #
    #  Aspect detection                                                    #
    # ------------------------------------------------------------------ #

    def _detect_aspects(self, text: str) -> list[AspectResult]:
        t = text.lower()
        tokens = set(re.findall(r'\b\w+\b', t))
        results = []
        for category, keywords in ASPECT_KEYWORDS.items():
            matched = [kw for kw in keywords if kw in tokens]
            if not matched:
                continue
            # Run VADER on surrounding sentences for aspect-level label
            sentences = [s for s in re.split(r'[.!?]', t)
                         if any(kw in s for kw in matched)]
            aspect_text = ' '.join(sentences) if sentences else text
            label, confidence, _, _, _ = self._vader_sentiment(aspect_text)
            results.append(AspectResult(
                category=category,
                label=label,
                confidence=confidence,
                keywords=matched,
            ))
        return results

    # ------------------------------------------------------------------ #
    #  SHAP token scores                                                   #
    # ------------------------------------------------------------------ #

    def _shap_scores(self, text: str) -> dict[str, float]:
        """Lightweight token scoring using VADER per token as proxy."""
        try:
            tokens = re.findall(r'\b\w+\b', text.lower())[:20]
            return {
                tok: round(self.vader.polarity_scores(tok)['compound'], 4)
                for tok in tokens
            }
        except Exception:
            return {}


    # ------------------------------------------------------------------ #
    #  Main predict                                                        #
    # ------------------------------------------------------------------ #

    def predict(self, request: ReviewRequest) -> PredictionResponse:
        if not self.ready:
            raise RuntimeError('Predictor not loaded.')

        label, confidence, pos, neu, neg = self._roberta_sentiment(request.text)
        model_used = 'roberta'

        if confidence < 0.60:
            label, confidence, pos, neu, neg = self._vader_sentiment(request.text)
            model_used = 'vader'

        aspects = self._detect_aspects(request.text)
        shap_scores = self._shap_scores(request.text)

        return PredictionResponse(
            review_id=request.review_id,
            label=label,
            confidence=confidence,
            pos_score=pos,
            neu_score=neu,
            neg_score=neg,
            model_used=model_used,
            aspects=aspects,
            shap_scores=shap_scores,
        )
