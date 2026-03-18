# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Iterable


def contains_mention(user_aliases: Iterable[str], content: str) -> bool:
    lowered = str(content or "").lower()
    for alias in user_aliases:
        token = f"@{alias}".strip().lower()
        if token and token in lowered:
            return True
    return False


def format_reactions(reactions: Any) -> str:
    if not isinstance(reactions, list) or not reactions:
        return ""
    chunks: list[str] = []
    for reaction in reactions:
        if not isinstance(reaction, dict):
            continue
        emoji = str(reaction.get("emoji") or "").strip()
        count = int(reaction.get("count") or 0)
        if not emoji:
            continue
        chunks.append(f"{emoji} {count}" if count > 0 else emoji)
    return "   ".join(chunks)
