"""Isolated competition extension. No network activity unless explicitly enabled."""
import json
import math
import time
from urllib.request import Request, urlopen

ENDPOINT = "https://api.tokenfactory.nebius.com/v1/chat/completions"


def audit_decision(decision, model, api_key, *, allow_live=False, transport=None):
    """Ask an NVIDIA model to review numerical evidence, never the user's prompt."""
    if not isinstance(model, str) or not model.lower().startswith("nvidia/"):
        raise ValueError("Use an exact NVIDIA model ID verified in the provider catalogue")
    if not api_key:
        raise ValueError("An API key is required; never include it in evidence")
    if transport is None and not allow_live:
        raise ValueError("Live requests disabled until free credits are verified")
    estimates = {}
    for key in ("centre_wh", "min_wh", "max_wh", "centre_co2_g", "min_co2_g", "max_co2_g"):
        value = decision.get("estimate", {}).get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if value < 0 or not math.isfinite(value):
                raise ValueError("Estimates must be finite and non-negative")
            estimates[key] = value
    if not estimates:
        raise ValueError("No numerical estimate evidence supplied")
    payload = {
        "model": model, "store": False, "max_tokens": 256,
        "messages": [
            {"role": "system", "content": "Review these illustrative energy and CO2 estimates for internal numerical consistency. They are not measurements. Identify limitations. Do not claim verified savings, regional compliance, or change any routing decision. Return a concise human-review note."},
            {"role": "user", "content": json.dumps(estimates, allow_nan=False)},
        ],
    }
    request = Request(ENDPOINT, data=json.dumps(payload).encode(), headers={
        "Authorization": "Bearer " + api_key, "Content-Type": "application/json",
    }, method="POST")
    start = time.monotonic()
    try:
        with (transport or urlopen)(request, timeout=30) as response:
            result = json.loads(response.read(1_000_000))
        note = result["choices"][0]["message"]["content"]
        if not isinstance(note, str) or not note.strip():
            raise ValueError("Missing response")
    except Exception:
        raise RuntimeError("Audit request failed; no route was changed") from None
    usage = result.get("usage") or {}
    return {
        "execution": "offline_test" if transport is not None else "live_provider_response",
        "requested_model": model,
        "elapsed_ms": round((time.monotonic() - start) * 1000),
        "usage": {k: v for k, v in usage.items() if k in (
            "prompt_tokens", "completion_tokens", "total_tokens") and type(v) is int and v >= 0},
        "review_note": note,
        "human_review_required": True,
        "route_changed": False,
        "measurement_claim": False,
        "user_prompt_transmitted": False,
    }
