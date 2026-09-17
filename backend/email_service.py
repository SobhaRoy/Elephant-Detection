import os
import resend
from datetime import datetime

# Resend API Key configured for your account
resend.api_key = "re_a9vaX3dK_5ABM2GrE7BgYzh2EmH9gU4gG"
TARGET_EMAIL = "roy688482@gmail.com"
email_dispatch_log = []

def send_elephant_email_alert(detection_id: int, count: int, confidence: float, lat: float, lon: float):
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    subject = f"🚨 [ELEGUARD ALERT] Herd of {count} Elephant(s) Detected!"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; background: #0f1f1d; color: #ffffff; padding: 24px; border-radius: 8px; max-width: 550px;">
        <div style="background: #ef4444; color: #fff; padding: 12px 16px; border-radius: 6px; text-align: center; margin-bottom: 16px;">
            <h2 style="margin: 0; font-size: 18px;">🚨 CRITICAL WILDLIFE INTERLOCK ALERT</h2>
            <p style="margin: 4px 0 0; font-size: 11px;">West Bengal Forest Department & NF Railway Control</p>
        </div>
        <p style="font-size: 14px; margin-bottom: 16px;">An elephant herd has entered the railway corridor sector (Sevoke–Gulma Zone).</p>
        <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 16px;">
            <tr style="border-bottom: 1px solid #1e3d39;">
                <td style="padding: 8px 0; color: #83c5be;"><strong>Incident Ref:</strong></td>
                <td style="padding: 8px 0; text-align: right;"><strong>#{detection_id}</strong></td>
            </tr>
            <tr style="border-bottom: 1px solid #1e3d39;">
                <td style="padding: 8px 0; color: #83c5be;"><strong>Time (IST):</strong></td>
                <td style="padding: 8px 0; text-align: right;">{timestamp}</td>
            </tr>
            <tr style="border-bottom: 1px solid #1e3d39;">
                <td style="padding: 8px 0; color: #83c5be;"><strong>Herd Count:</strong></td>
                <td style="padding: 8px 0; text-align: right; color: #ef4444; font-weight: bold; font-size: 16px;">{count} Elephant(s)</td>
            </tr>
            <tr style="border-bottom: 1px solid #1e3d39;">
                <td style="padding: 8px 0; color: #83c5be;"><strong>Inference Confidence:</strong></td>
                <td style="padding: 8px 0; text-align: right;">{int(confidence * 100)}%</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #83c5be;"><strong>Corridor Position:</strong></td>
                <td style="padding: 8px 0; text-align: right;">{lat:.4f}° N, {lon:.4f}° E</td>
            </tr>
        </table>
        <div style="background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; color: #fca5a5; padding: 10px; border-radius: 6px; font-weight: bold; font-size: 12px; text-align: center;">
            IMMEDIATE ACTION: Signal approaching train pilots to halt/reduce speed.
        </div>
    </div>
    """

    status = "FAILED"
    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": [TARGET_EMAIL],
            "subject": subject,
            "html": html_content
        }
        res = resend.Emails.send(params)
        print(f"\n[EMAIL DELIVERED] Successfully sent to inbox: {TARGET_EMAIL} (Resend ID: {res.get('id', 'ok')})")
        status = "DELIVERED_TO_INBOX"
    except Exception as err:
        print(f"\n[EMAIL ERROR] {err}")
        status = f"ERROR: {err}"

    entry = {
        "id": len(email_dispatch_log) + 1,
        "detection_id": detection_id,
        "recipient": TARGET_EMAIL,
        "timestamp": timestamp,
        "subject": subject,
        "status": status
    }
    email_dispatch_log.insert(0, entry)
    return entry

def get_email_logs():
    return email_dispatch_log[:50]
