"""
Benchmark VADER vs RoBERTa on a small labeled sample.
Run inside the inference container: python benchmark.py
"""
import json
from predictor import Predictor
from schemas import ReviewRequest

# Hand-labeled sample — ground truth
LABELED_REVIEWS = [
    ("Absolutely loved this hotel, staff were wonderful and room was spotless.", "positive"),
    ("Terrible experience, room was dirty and staff ignored our complaints.", "negative"),
    ("Decent stay, nothing special but breakfast was good.", "neutral"),
    ("Best hotel I've stayed in, will definitely come back!", "positive"),
    ("Awful service, will never book here again.", "negative"),
    ("The location was convenient but the rooms were quite small.", "neutral"),
    ("Exceptional service from check-in to check-out, highly recommend.", "positive"),
    ("Filthy bathroom, broken AC, and rude reception staff.", "negative"),
    ("Average hotel for the price, met basic expectations.", "neutral"),
    ("Stunning views, friendly staff, perfect for a weekend getaway.", "positive"),
    ("Mosquitoes everywhere and the wifi didn't work at all.", "negative"),
    ("It was okay, breakfast options were limited but room was clean.", "neutral"),
    ("Outstanding hospitality, the concierge went above and beyond.", "positive"),
    ("Booked a deluxe room but got a tiny cramped one instead, very disappointed.", "negative"),
    ("Standard business hotel, clean and functional, nothing extraordinary.", "neutral"),
    ("Loved the rooftop pool and the staff were incredibly attentive.", "positive"),
    ("Noisy rooms, paper-thin walls, couldn't sleep at all.", "negative"),
    ("Fine for a short stay, check-in was quick and efficient.", "neutral"),
    ("Perfect honeymoon destination, the staff made it so special.", "positive"),
    ("Charged extra for everything, felt like a money grab.", "negative"),
]


def run_benchmark():
    predictor = Predictor()
    predictor.load()

    vader_correct = 0
    roberta_correct = 0
    total = len(LABELED_REVIEWS)

    results = []

    for text, true_label in LABELED_REVIEWS:
        # RoBERTa prediction
        roberta_label, roberta_conf, *_ = predictor._roberta_sentiment(text)

        # VADER prediction
        vader_label, vader_conf, *_ = predictor._vader_sentiment(text)

        roberta_match = roberta_label == true_label
        vader_match = vader_label == true_label

        if roberta_match:
            roberta_correct += 1
        if vader_match:
            vader_correct += 1

        results.append({
            "text": text[:60] + "...",
            "true_label": true_label,
            "roberta_prediction": roberta_label,
            "roberta_confidence": roberta_conf,
            "roberta_correct": roberta_match,
            "vader_prediction": vader_label,
            "vader_confidence": vader_conf,
            "vader_correct": vader_match,
        })

    roberta_accuracy = round(roberta_correct / total * 100, 1)
    vader_accuracy = round(vader_correct / total * 100, 1)

    summary = {
        "total_reviews": total,
        "roberta_accuracy": roberta_accuracy,
        "vader_accuracy": vader_accuracy,
        "accuracy_delta": round(roberta_accuracy - vader_accuracy, 1),
        "results": results,
    }

    with open("benchmark_results.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*50}")
    print(f"BENCHMARK RESULTS — {total} labeled reviews")
    print(f"{'='*50}")
    print(f"RoBERTa accuracy: {roberta_accuracy}%")
    print(f"VADER accuracy:   {vader_accuracy}%")
    print(f"Delta:            +{summary['accuracy_delta']}%")
    print(f"\nFull results saved to benchmark_results.json")


if __name__ == "__main__":
    run_benchmark()