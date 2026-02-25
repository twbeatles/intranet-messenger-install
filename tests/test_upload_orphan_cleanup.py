# -*- coding: utf-8 -*-

import os
import time
from pathlib import Path


def _touch_old(path: Path, seconds_ago: int = 120) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(b'test')
    past = time.time() - max(1, int(seconds_ago))
    os.utime(path, (past, past))


def test_cleanup_orphan_upload_files_removes_untracked_file(app):
    import app.upload_tokens as upload_tokens
    from config import UPLOAD_FOLDER

    orphan = Path(UPLOAD_FOLDER) / 'orphan_untracked.txt'
    _touch_old(orphan, seconds_ago=600)
    assert orphan.exists()

    removed = upload_tokens.cleanup_orphan_upload_files(grace_seconds=0)
    assert removed >= 1
    assert not orphan.exists()


def test_cleanup_orphan_upload_files_keeps_active_token_file(app, monkeypatch):
    import app.upload_tokens as upload_tokens
    from config import UPLOAD_FOLDER

    monkeypatch.setattr(upload_tokens, 'TOKEN_TTL_SECONDS', 300)

    tracked = Path(UPLOAD_FOLDER) / 'tracked_token_file.txt'
    _touch_old(tracked, seconds_ago=600)
    token = upload_tokens.issue_upload_token(
        user_id=1,
        room_id=10,
        file_path=tracked.name,
        file_name=tracked.name,
        file_type='file',
        file_size=tracked.stat().st_size,
    )
    assert token

    upload_tokens.cleanup_orphan_upload_files(grace_seconds=0)
    assert tracked.exists()


def test_cleanup_orphan_upload_files_removes_consumed_untracked_file(app, monkeypatch):
    import app.upload_tokens as upload_tokens
    from config import UPLOAD_FOLDER

    monkeypatch.setattr(upload_tokens, 'TOKEN_TTL_SECONDS', 300)

    consumed = Path(UPLOAD_FOLDER) / 'consumed_orphan.txt'
    _touch_old(consumed, seconds_ago=600)
    token = upload_tokens.issue_upload_token(
        user_id=1,
        room_id=99,
        file_path=consumed.name,
        file_name=consumed.name,
        file_type='file',
        file_size=consumed.stat().st_size,
    )
    assert token
    data = upload_tokens.consume_upload_token(token, user_id=1, room_id=99, expected_type='file')
    assert data is not None

    removed = upload_tokens.cleanup_orphan_upload_files(grace_seconds=0)
    assert removed >= 1
    assert not consumed.exists()
