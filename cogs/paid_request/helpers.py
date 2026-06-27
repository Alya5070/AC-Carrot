import re

def parse_duration_to_days(duration_str: str) -> float:
    pattern = re.compile(r'^(\d+(?:\.\d+)?)\s*(s|m|h|d|w|mo|y)$', re.IGNORECASE)
    match = pattern.match(duration_str.strip())
    if not match:
        raise ValueError("Invalid duration format. Use e.g. 10s, 5m, 2h, 30d, 1y")
    
    value = float(match.group(1))
    unit = match.group(2).lower()
    
    if unit == 's':
        return value / 86400.0
    elif unit == 'm':
        return value / 1440.0
    elif unit == 'h':
        return value / 24.0
    elif unit == 'd':
        return value
    elif unit == 'w':
        return value * 7.0
    elif unit == 'mo':
        return value * 30.0
    elif unit == 'y':
        return value * 365.0
    return 30.0


def sanitize_input(text: str, max_len: int = 1000) -> str:
    if not text:
        return ""
    text = text.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return text
