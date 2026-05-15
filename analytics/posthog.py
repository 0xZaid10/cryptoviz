# cryptoviz/analytics/posthog.py

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
PARENT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PARENT))
try:
    import cryptoviz.config as config
except ModuleNotFoundError:
    import config


class Analytics:
    """
    PostHog event tracking. Gracefully disabled if no API key configured.
    """

    def __init__(self):
        self.enabled = bool(config.POSTHOG_API_KEY)
        self.client = None

        if self.enabled:
            try:
                import posthog
                posthog.api_key = config.POSTHOG_API_KEY
                posthog.host = config.POSTHOG_HOST
                self.client = posthog
                print("[Analytics] PostHog enabled")
            except ImportError:
                self.enabled = False
                print("[Analytics] PostHog not installed, analytics disabled")
        else:
            print("[Analytics] No PostHog key configured, analytics disabled")

    def track_alert_generated(self, event_type: str, asset: str, chat_id: str = "system"):
        if not self.enabled:
            return
        self.client.capture(
            distinct_id=chat_id,
            event="alert_generated",
            properties={
                "event_type": event_type,
                "asset": asset,
            }
        )

    def track_video_sent(self, asset: str, duration_secs: float, chat_id: str = "system"):
        if not self.enabled:
            return
        self.client.capture(
            distinct_id=chat_id,
            event="video_sent",
            properties={
                "asset": asset,
                "duration_secs": duration_secs,
            }
        )

    def track_user_subscribed(self, chat_id: str):
        if not self.enabled:
            return
        self.client.capture(
            distinct_id=chat_id,
            event="user_subscribed"
        )

    def track_pipeline_error(self, stage: str, error: str):
        if not self.enabled:
            return
        self.client.capture(
            distinct_id="system",
            event="pipeline_error",
            properties={
                "stage": stage,
                "error": error[:200]
            }
        )
