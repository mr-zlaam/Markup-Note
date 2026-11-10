"""Utility functions for human-readable relative timestamp formatting."""

from datetime import datetime, timezone


def format_relative_time(timestamp: float) -> str:
    """Format a Unix epoch timestamp into a human-friendly relative string.

    Examples:
        - "Just now" (< 1 minute)
        - "12m ago" (< 1 hour)
        - "2:30 PM" (earlier today)
        - "Yesterday" (yesterday)
        - "Oct 24" (earlier this year)
        - "10/24/2024" (previous years)
    """
    now = datetime.now()
    dt = datetime.fromtimestamp(timestamp)
    delta = now - dt

    total_seconds = int(delta.total_seconds())

    if total_seconds < 60:
        return "Just now"
    if total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes}m ago"

    # If within the same calendar day
    if dt.date() == now.date():
        return dt.strftime("%-I:%M %p")

    # If yesterday
    days_diff = (now.date() - dt.date()).days
    if days_diff == 1:
        return "Yesterday"

    # If within current calendar year
    if dt.year == now.year:
        return dt.strftime("%b %-d")

    # Older years
    return dt.strftime("%x")
