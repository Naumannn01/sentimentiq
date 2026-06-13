from pydantic import BaseModel
from typing import Optional


class ReviewRequest(BaseModel):
    review_id: str
    text: str
    language: str = 'en'


class AspectResult(BaseModel):
    category: str
    label: str
    confidence: float
    keywords: list[str]


class PredictionResponse(BaseModel):
    review_id: str
    label: str                        # positive / neutral / negative
    confidence: float
    pos_score: float
    neu_score: float
    neg_score: float
    model_used: str                   # roberta or vader
    aspects: list[AspectResult]
    shap_scores: dict[str, float]     # token → weight