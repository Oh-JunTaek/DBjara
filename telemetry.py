"""
Anonymous Telemetry & Usage Analytics for DBjara
Collects non-personally-identifiable usage statistics (e.g. block counts) to measure app utility.
"""

import json
import uuid
import threading
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

# Public GA4 Measurement ID & API Secret placeholder for DBjara telemetry
# Can be replaced with actual GA4 ID or a free Cloudflare Worker/Serverless endpoint
GA_MEASUREMENT_ID = "G-DBJARA0000"
GA_API_SECRET = "dbjara_telemetry_secret"
GA_ENDPOINT = f"https://www.google-analytics.com/mp/collect?measurement_id={GA_MEASUREMENT_ID}&api_secret={GA_API_SECRET}"


def get_anonymous_client_id(config: dict) -> str:
    """Get or generate an anonymous random client UUID."""
    if "telemetry_uuid" not in config or not config["telemetry_uuid"]:
        config["telemetry_uuid"] = str(uuid.uuid4())
    return config["telemetry_uuid"]


def send_event_async(config: dict, event_name: str, params: Optional[Dict[str, Any]] = None):
    """Send an anonymous telemetry event asynchronously without blocking UI or main loop."""
    if not config.get("telemetry_enabled", True):
        return

    def _worker():
        try:
            client_id = get_anonymous_client_id(config)
            event_params = {
                "version": "v1.0.0",
                "mode": config.get("mode", "medium"),
                "night_lock": config.get("night_lock", True),
                "otp_enabled": config.get("otp_enabled", False),
            }
            if params:
                event_params.update(params)

            payload = {
                "client_id": client_id,
                "events": [
                    {
                        "name": event_name,
                        "params": event_params
                    }
                ]
            }

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                GA_ENDPOINT,
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "DBjara-Telemetry"},
                method="POST"
            )
            # Timeout after 2 seconds to ensure no lag
            with urllib.request.urlopen(req, timeout=2.0) as _:
                pass
        except Exception:
            # Telemetry errors must fail silently and never disrupt user experience
            pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
