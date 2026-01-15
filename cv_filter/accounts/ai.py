import json
import requests
from django.conf import settings


class MakeAIError(RuntimeError):
    pass


def _auth_headers() -> dict:
    # egyszerű shared-secret header
    secret = getattr(settings, "MAKE_WEBHOOK_SECRET", "")
    return {"X-Make-Secret": secret} if secret else {}


def parse_nlq(query: str, language: str = "hu") -> dict:
    url = getattr(settings, "MAKE_NLQ_WEBHOOK_URL", "")
    if not url:
        raise MakeAIError("MAKE_NLQ_WEBHOOK_URL is not set")

    payload = {"query": query, "language": language}
    try:
        r = requests.post(
            url,
            json=payload,
            headers=_auth_headers(),
            timeout=getattr(settings, "MAKE_TIMEOUT_SECONDS", 20),
        )
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        raise MakeAIError(f"NLQ parse failed: {e}") from e

    if not isinstance(data, dict) or "filters" not in data:
        raise MakeAIError("Invalid NLQ response (missing 'filters')")
    return data


def generate_summary(cv_text: str, language: str = "hu", job_text: str | None = None) -> dict:
    url = getattr(settings, "MAKE_SUMMARY_WEBHOOK_URL", "")
    if not url:
        raise MakeAIError("MAKE_SUMMARY_WEBHOOK_URL is not set")

    payload = {"cv_text": cv_text, "job_text": job_text, "language": language}
    try:
        r = requests.post(
            url,
            json=payload,
            headers=_auth_headers(),
            timeout=getattr(settings, "MAKE_TIMEOUT_SECONDS", 30),
        )
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        raise MakeAIError(f"Summary generation failed: {e}") from e

    if not isinstance(data, dict) or "summary" not in data:
        raise MakeAIError("Invalid summary response (missing 'summary')")
    return data
