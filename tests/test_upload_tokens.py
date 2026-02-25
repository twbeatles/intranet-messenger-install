# -*- coding: utf-8 -*-

import time
from pathlib import Path


def test_issue_and_consume_upload_token_once(app, monkeypatch):
    import app.upload_tokens as upload_tokens
    from config import UPLOAD_FOLDER

    monkeypatch.setattr(upload_tokens, "TOKEN_TTL_SECONDS", 300)
    file_path = Path(UPLOAD_FOLDER) / "abc.txt"
    file_path.write_bytes(b"abc")
    token = upload_tokens.issue_upload_token(
        user_id=1,
        room_id=10,
        file_path=file_path.name,
        file_name="abc.txt",
        file_type="file",
        file_size=123,
    )

    data = upload_tokens.consume_upload_token(token, user_id=1, room_id=10, expected_type="file")
    assert data is not None
    assert data["file_name"] == "abc.txt"
    assert data["file_path"] == "abc.txt"

    # 1회성 소비 보장
    data2 = upload_tokens.consume_upload_token(token, user_id=1, room_id=10, expected_type="file")
    assert data2 is None


def test_upload_token_expires(app, monkeypatch):
    import app.upload_tokens as upload_tokens
    from config import UPLOAD_FOLDER

    monkeypatch.setattr(upload_tokens, "TOKEN_TTL_SECONDS", 0)
    file_path = Path(UPLOAD_FOLDER) / "exp.txt"
    file_path.write_bytes(b"exp")
    token = upload_tokens.issue_upload_token(
        user_id=1,
        room_id=10,
        file_path=file_path.name,
        file_name="exp.txt",
        file_type="file",
        file_size=10,
    )
    time.sleep(0.01)
    assert upload_tokens.consume_upload_token(token, user_id=1, room_id=10, expected_type="file") is None
