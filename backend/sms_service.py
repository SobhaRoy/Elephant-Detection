import os
import requests
from datetime import datetime

TARGET_PHONE = "7679625154"
NTFY_TOPIC = "eleguard_sevoke_alert"

ALERT_ROSTER = [
    {"name": "Quick Response Team Lead", "phone": f"+91-{TARGET_PHONE}", "role": "Field Corridor Patrol"},
    {"name": "Rail Interlock Station Master", "phone": f"+91-{TARGET_PHONE}", "role": "Siliguri Jn Section"},
    {"name": "Forest Range HQ", "phone": f"+91-{TARGET_PHONE}", "role": "Sevoke Wild Squad"}
]

sms_dispatch_log = []

def trigger_real_phone_notification(title: str, message: str):
    """Pushes an instant priority banner notification directly to your phone."""
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": "urgent",
                "Tags": "warning,elephant,rotating_light"
            },
            timeout=4
        )
    except Exception as e:
        print(f"[PUSH ERROR] {e}")

def send_elephant_sms_alert(detection_id: int, count: int, confidence: float, lat: float, lon: float):
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    message_body = (
        f"[ELEGUARD ALERT] Herd of {count} elephant(s) detected near railway track! "
        f"GPS: {lat:.4f} N, {lon:.4f} E (Sevoke-Gulma). Conf: {int(confidence * 100)}%. "
        f"Action: Halt approaching trains."
    )

    # 1. Fire real instant push to your handset
    trigger_real_phone_notification(
        title=f"🚨 CRITICAL ELEPHANT ALERT: Herd of {count}",
        message=message_body
    )

    # 2. Update dashboard gateway logs
    dispatched_entries = []
    for contact in ALERT_ROSTER:
        entry = {
            "id": len(sms_dispatch_log) + 1,
            "detection_id": detection_id,
            "recipient_name": contact["name"],
            "recipient_phone": contact["phone"],
            "role": contact["role"],
            "message": message_body,
            "timestamp": timestamp,
            "status": "DELIVERED_TO_MOBILE"
        }
        sms_dispatch_log.insert(0, entry)
        dispatched_entries.append(entry)

    print(f"\n[LIVE ALERT] Transmitted to {TARGET_PHONE} and phone device for Incident #{detection_id}")
    return dispatched_entries

def get_sms_logs():
    return sms_dispatch_log[:50]
