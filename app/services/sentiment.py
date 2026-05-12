# app/services/sentiment.py

from transformers import pipeline
from functools import lru_cache
import logging

# Set up logging so we can see what the AI engine is doing
logger = logging.getLogger(__name__)


# --- Lazy Singleton Pattern ---
# @lru_cache ensures the model is loaded ONCE and reused for every request.
# Loading an AI model takes ~3-5 seconds. Without this cache, every API
# call would reload the model — making your server unbearably slow.
@lru_cache(maxsize=1)
def _get_sentiment_pipeline():
    """
    Load the HuggingFace sentiment analysis model.
    Called once on first use, then cached for the lifetime of the server.
    """
    logger.info("Loading sentiment model — this happens only once...")
    return pipeline(
        task="sentiment-analysis",
        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
        # If you don't have a GPU, this ensures it runs on your CPU
        device=-1,
    )


def analyze_sentiment(text: str) -> dict:
    """
    Analyze the sentiment of a given text string.

    Args:
        text: Any string — a news headline, tweet, or speech excerpt.

    Returns:
        A dict with:
          - label: "positive", "negative", or "neutral"
          - score: confidence between 0.0 and 1.0
          - analyzed_text: the original input (for traceability)

    Example:
        analyze_sentiment("The candidate delivered a powerful speech")
        → {"label": "positive", "score": 0.97, "analyzed_text": "..."}
    """
    if not text or not text.strip():
        return {
            "label": "neutral",
            "score": 0.0,
            "analyzed_text": text,
        }

    # Truncate text to 512 characters — transformer models have token limits.
    # Silently truncating is better than crashing on long inputs.
    truncated = text.strip()[:512]

    try:
        sentiment_pipeline = _get_sentiment_pipeline()
        results = sentiment_pipeline(truncated)

        # The pipeline returns a list like:
        # [{"label": "LABEL_2", "score": 0.97}]
        # The Cardiff model uses LABEL_0=negative, LABEL_1=neutral, LABEL_2=positive
        raw = results[0]

        label_map = {
            "LABEL_0": "negative",
            "LABEL_1": "neutral",
            "LABEL_2": "positive",
            # Some model versions return human-readable labels directly
            "NEGATIVE": "negative",
            "NEUTRAL": "neutral",
            "POSITIVE": "positive",
        }

        readable_label = label_map.get(raw["label"].upper(), raw["label"].lower())

        return {
            "label": readable_label,
            "score": round(raw["score"], 4),
            "analyzed_text": truncated,
        }

    except Exception as e:
        # Never let AI failures crash the whole API.
        # Log the error and return a safe fallback.
        logger.error(f"Sentiment analysis failed: {e}")
        return {
            "label": "neutral",
            "score": 0.0,
            "analyzed_text": truncated,
        }