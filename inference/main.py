from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from schemas import ReviewRequest, PredictionResponse
from predictor import Predictor

predictor = Predictor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    predictor.load()
    yield


app = FastAPI(title="SentimentIQ Inference", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "model": predictor.model_name, "ready": predictor.ready}


@app.post("/predict", response_model=PredictionResponse)
def predict(request: ReviewRequest):
    try:
        return predictor.predict(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch", response_model=list[PredictionResponse])
def predict_batch(requests: list[ReviewRequest]):
    try:
        return [predictor.predict(r) for r in requests]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))