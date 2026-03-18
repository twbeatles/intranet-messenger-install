# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PendingSend:
    payload: dict[str, Any]
    created_at: float
    last_attempt_at: float = 0.0
    retry_count: int = 0
    failed: bool = False
    is_file: bool = False
    file_name: str = ""

    @classmethod
    def from_store_row(cls, row: dict[str, Any]) -> "PendingSend | None":
        client_payload = row.get("payload")
        payload = client_payload if isinstance(client_payload, dict) else {}
        if not payload:
            return None
        return cls(
            payload=payload,
            created_at=float(row.get("created_at") or 0.0),
            last_attempt_at=float(row.get("last_attempt_at") or 0.0),
            retry_count=int(row.get("retry_count") or 0),
            failed=bool(row.get("failed")),
            is_file=bool(payload.get("type") in ("file", "image")),
            file_name=str(payload.get("content") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload": dict(self.payload),
            "created_at": float(self.created_at),
            "last_attempt_at": float(self.last_attempt_at),
            "retry_count": int(self.retry_count),
            "failed": bool(self.failed),
            "is_file": bool(self.is_file),
            "file_name": str(self.file_name),
        }


RoomSummary = dict[str, Any]
SocketPayload = dict[str, Any]
