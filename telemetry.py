"""
DBjara - 비식별 익명 사용 통계 수집 모듈
프로그램의 유용성(차단 횟수 등)을 측정하기 위해 개인정보를 제외한 익명 이벤트만 전송합니다.
"""

import json
import uuid
import threading
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

# GA4 Measurement ID 및 API Secret (커스텀 서버리스 엔드포인트로 대체 가능)
GA_MEASUREMENT_ID = "G-DBJARA0000"
GA_API_SECRET = "dbjara_telemetry_secret"
GA_ENDPOINT = f"https://www.google-analytics.com/mp/collect?measurement_id={GA_MEASUREMENT_ID}&api_secret={GA_API_SECRET}"


def get_anonymous_client_id(config: dict) -> str:
    """익명 기기 식별용 UUID를 가져오거나 새로 생성합니다."""
    if "telemetry_uuid" not in config or not config["telemetry_uuid"]:
        config["telemetry_uuid"] = str(uuid.uuid4())
    return config["telemetry_uuid"]


def send_event_async(config: dict, event_name: str, params: Optional[Dict[str, Any]] = None):
    """메인 스레드를 방해하지 않도록 비동기 스레드에서 익명 이벤트를 전송합니다."""
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
            # 2초 타임아웃으로 UI 렉 방지
            with urllib.request.urlopen(req, timeout=2.0) as _:
                pass
        except Exception:
            # 통계 전송 실패 시 사용자 경험에 영향을 주지 않도록 무시
            pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
