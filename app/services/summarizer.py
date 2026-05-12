import os
from groq import Groq
from dotenv import load_dotenv

# Load secrets from .env
load_dotenv()

def get_groq_client() -> Groq:
    """
    Creates and returns a Groq client.
    Reads GROQ_API_KEY from the .env file.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from your .env file.")
    return Groq(api_key=api_key)


def generate_election_summary(
    election_id: int,
    election_name: str,
    candidates: list[dict],
    articles: list[dict],
) -> dict:
    """
    Sends election data to Groq (Llama 3.3 70b) and returns a structured summary.
    """

    # ── Build candidates section ──
    if candidates:
        candidate_lines = []
        for c in candidates:
            sentiment = "not analyzed"
            if c.get("sentiment"):
                sentiment = (
                    f"{c['sentiment']['label']} "
                    f"(score: {c['sentiment']['score']})"
                )
            candidate_lines.append(
                f"- {c['name']} ({c['party']}): sentiment = {sentiment}"
            )
        candidates_text = "\n".join(candidate_lines)
    else:
        candidates_text = "No candidates registered yet."

    # ── Build news section ──
    if articles:
        article_lines = []
        for a in articles:
            credibility = a.get("credibility") or "not analyzed"
            article_lines.append(
                f"- [{credibility.upper()}] {a['headline']} "
                f"(source: {a['source']})"
            )
        articles_text = "\n".join(article_lines)
    else:
        articles_text = "No news articles found for this election."

    # ── Build prompt ──
    prompt = f"""
You are an election intelligence analyst. Analyze the following data
for election: "{election_name}" (ID: {election_id}).

CANDIDATES:
{candidates_text}

NEWS ARTICLES:
{articles_text}

Write a concise briefing with exactly these three sections:

SUMMARY:
2-3 sentences giving an overall picture of this election's current state.

KEY TOPICS:
A comma-separated list of 3-5 main themes or issues (e.g. economy, corruption, healthcare).

OVERALL SENTIMENT:
One word only — either: positive, negative, or neutral.
""".strip()

    # ── Call Groq ──
    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Free and very capable
            max_tokens=400,
            temperature=0.4,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional election analyst. "
                        "Be concise, factual, and structured."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        raw_text = response.choices[0].message.content.strip()
        summary, key_topics, overall_sentiment = _parse_response(raw_text)

        return {
            "election_id":       election_id,
            "election_name":     election_name,
            "summary":           summary,
            "key_topics":        key_topics,
            "overall_sentiment": overall_sentiment,
            "model_used":        "llama-3.3-70b-versatile (Groq)",
            "raw_response":      raw_text,
        }

    except Exception as e:
        print(f"[summarizer] Groq call failed: {e}")
        return {
            "election_id":       election_id,
            "election_name":     election_name,
            "summary":           "Summary unavailable due to an AI error.",
            "key_topics":        [],
            "overall_sentiment": "neutral",
            "model_used":        "llama-3.3-70b-versatile (Groq)",
            "raw_response":      str(e),
        }


def _parse_response(text: str) -> tuple[str, list[str], str]:
    """
    Parses Groq's structured text into three clean values.
    """
    summary           = "Not available"
    key_topics        = []
    overall_sentiment = "neutral"

    lines = text.splitlines()
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.upper().startswith("SUMMARY:"):
            current_section = "summary"
            inline = line[len("SUMMARY:"):].strip()
            if inline:
                summary = inline
        elif line.upper().startswith("KEY TOPICS:"):
            current_section = "topics"
            inline = line[len("KEY TOPICS:"):].strip()
            if inline:
                key_topics = [t.strip() for t in inline.split(",") if t.strip()]
        elif line.upper().startswith("OVERALL SENTIMENT:"):
            current_section = "sentiment"
            inline = line[len("OVERALL SENTIMENT:"):].strip()
            if inline:
                overall_sentiment = inline.lower()
        else:
            if current_section == "summary" and summary == "Not available":
                summary = line
            elif current_section == "topics" and not key_topics:
                key_topics = [t.strip() for t in line.split(",") if t.strip()]
            elif current_section == "sentiment" and overall_sentiment == "neutral":
                overall_sentiment = line.lower()

    return summary, key_topics, overall_sentiment