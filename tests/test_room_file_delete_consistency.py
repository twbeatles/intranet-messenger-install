# -*- coding: utf-8 -*-

from __future__ import annotations

import io


def _register(client, username: str, password: str = "Password123!"):
    response = client.post(
        "/api/register",
        json={"username": username, "password": password, "nickname": username},
    )
    assert response.status_code == 200


def _login(client, username: str, password: str = "Password123!"):
    response = client.post("/api/login", json={"username": username, "password": password})
    assert response.status_code == 200


def _create_room(client) -> int:
    response = client.post("/api/rooms", json={"members": []})
    assert response.status_code == 200
    return int(response.json["room_id"])


def _build_socket_client(app, flask_client):
    from app import socketio

    socket_client = socketio.test_client(app, flask_test_client=flask_client)
    assert socket_client.is_connected()
    return socket_client


def test_delete_room_file_tombstones_linked_message_and_emits_events(app):
    from app.models import get_db

    client = app.test_client()
    _register(client, "deletefile")
    _login(client, "deletefile")
    room_id = _create_room(client)

    upload_response = client.post(
        "/api/upload",
        data={"room_id": str(room_id), "file": (io.BytesIO(b"hello"), "linked.txt")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200
    upload_payload = upload_response.json

    socket_client = _build_socket_client(app, client)
    try:
        ack = socket_client.emit(
            "send_message",
            {
                "room_id": room_id,
                "content": "",
                "type": "file",
                "upload_token": upload_payload["upload_token"],
                "encrypted": False,
            },
            callback=True,
        )
        assert isinstance(ack, dict)
        assert ack.get("ok") is True
        socket_client.get_received()

        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, message_id FROM room_files WHERE room_id = ? ORDER BY id DESC LIMIT 1",
                (room_id,),
            )
            room_file = cursor.fetchone()
            assert room_file is not None
            file_id = int(room_file["id"])
            message_id = int(room_file["message_id"] or 0)
            assert message_id > 0

        delete_response = client.delete(f"/api/rooms/{room_id}/files/{file_id}")
        assert delete_response.status_code == 200
        delete_payload = delete_response.json
        assert delete_payload["success"] is True
        assert int(delete_payload["message_id"]) == message_id

        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT encrypted, file_path, file_name, message_type FROM messages WHERE id = ?",
                (message_id,),
            )
            message_row = cursor.fetchone()
            assert message_row is not None
            assert int(message_row["encrypted"] or 0) == 0
            assert message_row["file_path"] is None
            assert message_row["file_name"] is None
            assert message_row["message_type"] == "text"

        received = socket_client.get_received()
        names = [event["name"] for event in received]
        assert "message_deleted" in names
        assert "room_updated" in names
    finally:
        socket_client.disconnect()
