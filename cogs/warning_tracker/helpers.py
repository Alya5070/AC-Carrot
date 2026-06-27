import discord

def sanitize_reason(text: str) -> str:
    if not text:
        return ""
    text = text.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
    if len(text) > 500:
        text = text[:500] + "..."
    return text

def get_ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def is_repeated_offense(current_reason: str, previous_warnings: list) -> bool:
    curr = current_reason.lower().strip()
    for _, content, _ in previous_warnings:
        prev = content.lower().strip()
        if curr in prev or prev in curr:
            return True
    return False

def get_channel_mention(channel) -> str:
    if not channel:
        return "Unknown Channel"
    if isinstance(channel, discord.Thread) and channel.parent:
        return channel.parent.mention
    return getattr(channel, "mention", str(channel))
