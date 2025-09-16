# Description: A place for helper functions.
from typing import Literal

import httpx

# Stripe subscription statuses we care about
StripeStatus = Literal[
    "active",
    "trialing",
    "past_due",
    "unpaid",
    "canceled",
    "incomplete",
    "incomplete_expired",
    "paused",  # appears when collection is paused
    "not_found",  # our sentinel for 404
    "error",  # our sentinel for any other error
    "unknown",  # our sentinel for unexpected/missing status
]

# Count these as "live"/entitled to service
_ENTITLED = {"active", "trialing", "past_due"}


def is_entitled_status(status: str) -> bool:
    """Return True if the status should keep service enabled."""
    return status in _ENTITLED


async def check_live(subscription_id: str, api_key: str) -> StripeStatus:
    """
    Fetch the Stripe subscription and return its status string.

    Possible returns:
      - "active", "trialing", "past_due", "unpaid", "canceled",
        "incomplete", "incomplete_expired", "paused"
      - "not_found"  -> subscription does not exist (HTTP 404)
      - "error"      -> network/HTTP error, JSON error, etc.
      - "unknown"    -> Stripe returned a status we didn't expect or missing
    """
    try:
        async with httpx.AsyncClient(
            base_url="https://api.stripe.com",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        ) as client:
            r = await client.get(f"/v1/subscriptions/{subscription_id}")
            if r.status_code == 404:
                return "not_found"
            r.raise_for_status()
            status = (r.json().get("status") or "").lower().strip()

            # Recognized statuses
            known = {
                "active",
                "trialing",
                "past_due",
                "unpaid",
                "canceled",
                "incomplete",
                "incomplete_expired",
                "paused",
            }
            if status in known:
                return status  # type: ignore[return-value]

            return "unknown"
    except Exception:
        return "error"
