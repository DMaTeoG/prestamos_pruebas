"""Send CI/CD and performance telemetry notifications to Telegram.

If TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID are not configured, the script
logs the formatted message in dry-run mode and exits 0 so pipelines never
break before Telegram integration is connected.
"""

import argparse
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import json

# Intento de cargar variables de entorno desde .env local si existe
try:
    from dotenv import load_dotenv
    load_dotenv()
    root_env = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(root_env):
        load_dotenv(root_env)
except ImportError:
    # Si python-dotenv no está instalado, buscar .env manualmente como fallback
    root_env = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(root_env):
        with open(root_env, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val


def send_telegram_message(message: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        print("[telegram][dry-run] Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")
        print("[telegram][dry-run] Message that would be sent:")
        print(message)
        return True

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": message,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[telegram] Sent successfully (HTTP {resp.status}).")
            return 200 <= resp.status < 300
    except urllib.error.URLError as exc:
        print(f"[telegram][error] Failed to send message: {exc}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Send DevOps telemetry to Telegram.")
    parser.add_argument("--title", required=True, help="Notification title")
    parser.add_argument("--status", required=True, help="Status (SUCCESS, FAILED, ROLLBACK)")
    parser.add_argument("--version", default=os.getenv("APP_VERSION", "dev"), help="App version/SHA")
    parser.add_argument("--details", default="", help="Extra metrics or details")
    args = parser.parse_args()

    icon = {"SUCCESS": "✅", "ROLLBACK": "⚠️", "FAILED": "❌"}.get(args.status.upper(), "ℹ️")
    lines = [
        f"{icon} *{args.title}*",
        f"• *Estado:* `{args.status}`",
        f"• *Versión:* `{args.version}`",
    ]
    if args.details:
        lines.append(f"• *Detalles:* {args.details}")

    ok = send_telegram_message("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
