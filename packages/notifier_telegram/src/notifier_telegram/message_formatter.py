"""Message formatting for Telegram alerts.

The message formatter converts AlertPayload data into human-readable text
suitable for Telegram messages.
"""

from datetime import datetime, timezone

from notifier_telegram.alert_payload import AlertPayload


def format_alert_message(alert: AlertPayload) -> str:
    """Format an AlertPayload into a human-readable Telegram message.

    The output includes:
    - Alert indicator
    - Symbol
    - Imbalance ratio (as decimal)
    - Bid and ask volumes
    - Threshold that was exceeded
    - Timestamp

    Args:
        alert: The alert payload to format.

    Returns:
        A formatted message string suitable for Telegram.
    """
    # Format timestamp as ISO datetime
    dt = datetime.fromtimestamp(alert.timestamp, tz=timezone.utc)
    timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    # Format the message with all required information
    message = (
        f"Imbalance Alert!\n"
        f"\n"
        f"Symbol: {alert.symbol}\n"
        f"Imbalance Ratio: {alert.ratio}\n"
        f"Threshold: {alert.threshold}\n"
        f"\n"
        f"Bid Volume: {alert.bid_volume}\n"
        f"Ask Volume: {alert.ask_volume}\n"
        f"\n"
        f"Time: {timestamp_str}"
    )

    return message
