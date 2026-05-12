# app/services/fake_news.py

from functools import lru_cache
from transformers import pipeline

# ─────────────────────────────────────────
# WHY THESE LABELS?
# Zero-shot classification asks the model:
#   "Does this text entail the concept of <label>?"
# We pass three possible answers. The model picks the best fit.
# ─────────────────────────────────────────
CANDIDATE_LABELS = ["credible", "misleading", "fake"]


@lru_cache(maxsize=1)
def _load_model():
    """
    Load the BART-MNLI model exactly once and cache it.

    facebook/bart-large-mnli:
    - BART = encoder-decoder transformer
    - MNLI = trained on Multi-Genre Natural Language Inference dataset
    - "zero-shot" = no fine-tuning needed; works on any labels you give it

    First call: downloads ~1.6 GB, takes 30-60 seconds.
    Subsequent calls: instant (cached in memory).
    """
    print("Loading BART-MNLI model... (first time only)")
    return pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
    )


def detect_fake_news(text: str) -> dict:
    """
    Run zero-shot classification on a news article.

    Args:
        text: The article headline or content to analyze.

    Returns:
        dict with keys: label, score, analyzed_text

    Example return:
        {
            "label": "misleading",
            "score": 0.78,
            "analyzed_text": "Study shows vaccines cause autism..."
        }
    """
    try:
        # Truncate to 512 characters — BART has a token limit.
        # Beyond this, the model ignores the rest anyway.
        truncated = text[:512]

        classifier = _load_model()

        # result looks like:
        # {
        #   "labels": ["credible", "misleading", "fake"],
        #   "scores": [0.12, 0.78, 0.10]
        # }
        # The labels are sorted from highest score to lowest.
        result = classifier(truncated, candidate_labels=CANDIDATE_LABELS)

        # result["labels"][0] is the top prediction
        # result["scores"][0] is its confidence
        return {
            "label":         result["labels"][0],
            "score":         round(result["scores"][0], 4),
            "analyzed_text": truncated,
        }

    except Exception as e:
        # Never crash the whole server because of AI failure.
        # Return a safe fallback so the route still responds.
        print(f"[fake_news] Error: {e}")
        return {
            "label":         "credible",   # safe default
            "score":         0.0,
            "analyzed_text": text[:512],
        }