# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime

from flask import jsonify, session

from app.http.common import emit_socket_event, json_dict
from app.models import (
    close_poll,
    create_poll,
    get_poll,
    get_room_polls,
    get_user_votes,
    is_room_admin,
    is_room_member,
    vote_poll,
)
from app.utils import sanitize_input


def register_poll_routes(app) -> None:
    @app.route("/api/rooms/<int:room_id>/polls")
    def get_polls(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "접근 권한이 없습니다."}), 403

        polls = get_room_polls(room_id)
        for poll in polls:
            poll["my_votes"] = get_user_votes(poll["id"], session["user_id"])
        return jsonify(polls)

    @app.route("/api/rooms/<int:room_id>/polls", methods=["POST"])
    def create_poll_route(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "접근 권한이 없습니다."}), 403

        data = json_dict()
        question = sanitize_input(data.get("question", ""), max_length=200)
        options = data.get("options", [])
        multiple_choice = data.get("multiple_choice", False)
        anonymous = data.get("anonymous", False)
        ends_at = data.get("ends_at")

        if not question:
            return jsonify({"error": "질문을 입력해주세요."}), 400
        if len(options) < 2:
            return jsonify({"error": "최소 2개의 옵션이 필요합니다."}), 400

        if ends_at:
            try:
                ends_at_dt = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
                if ends_at_dt < datetime.now(ends_at_dt.tzinfo) if ends_at_dt.tzinfo else ends_at_dt < datetime.now():
                    return jsonify({"error": "마감 시간은 현재 시간 이후여야 합니다."}), 400
                ends_at = ends_at_dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                return jsonify({"error": "올바른 날짜/시간 형식이 아닙니다. (ISO 8601)"}), 400

        options = [sanitize_input(option, max_length=100) for option in options[:10]]
        poll_id = create_poll(room_id, session["user_id"], question, options, multiple_choice, anonymous, ends_at)
        if poll_id:
            poll = get_poll(poll_id)
            if poll:
                emit_socket_event(
                    "poll_created",
                    {"room_id": room_id, "poll": poll, "action": "poll_created", "by_user_id": int(session["user_id"])},
                    room_id=room_id,
                )
                return jsonify({"success": True, "poll": poll})
            return jsonify({"error": "투표 생성 후 조회에 실패했습니다."}), 500
        return jsonify({"error": "투표 생성에 실패했습니다."}), 500

    @app.route("/api/polls/<int:poll_id>/vote", methods=["POST"])
    def vote_poll_route(poll_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401

        poll = get_poll(poll_id)
        if not poll:
            return jsonify({"error": "투표를 찾을 수 없습니다."}), 404
        if not is_room_member(poll["room_id"], session["user_id"]):
            return jsonify({"error": "접근 권한이 없습니다."}), 403

        data = json_dict()
        option_ids = data.get("option_ids")
        option_id = data.get("option_id")
        selected: list[int] = []
        if isinstance(option_ids, list):
            for value in option_ids:
                try:
                    normalized = int(value)
                except (TypeError, ValueError):
                    continue
                if normalized > 0 and normalized not in selected:
                    selected.append(normalized)
        elif option_id is not None:
            try:
                normalized = int(option_id)
            except (TypeError, ValueError):
                normalized = 0
            if normalized > 0:
                selected.append(normalized)

        if not selected:
            return jsonify({"error": "옵션을 선택해주세요."}), 400

        success, error = vote_poll(poll_id, selected, session["user_id"])
        if success:
            poll = get_poll(poll_id)
            if not poll:
                return jsonify({"error": "투표 정보를 불러오지 못했습니다."}), 500
            poll["my_votes"] = get_user_votes(poll_id, session["user_id"])
            emit_socket_event(
                "poll_updated",
                {
                    "room_id": int(poll.get("room_id") or 0),
                    "poll": poll,
                    "action": "poll_voted",
                    "by_user_id": int(session["user_id"]),
                },
                room_id=int(poll.get("room_id") or 0),
            )
            return jsonify({"success": True, "poll": poll})
        return jsonify({"error": error}), 400

    @app.route("/api/polls/<int:poll_id>/close", methods=["POST"])
    def close_poll_route(poll_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401

        poll = get_poll(poll_id)
        if not poll:
            return jsonify({"error": "투표를 찾을 수 없습니다."}), 404
        if not is_room_member(poll["room_id"], session["user_id"]):
            return jsonify({"error": "접근 권한이 없습니다."}), 403

        is_admin = is_room_admin(poll["room_id"], session["user_id"])
        success, error = close_poll(poll_id, session["user_id"], is_admin=is_admin)
        if success:
            updated_poll = get_poll(poll_id)
            if updated_poll:
                emit_socket_event(
                    "poll_updated",
                    {
                        "room_id": int(updated_poll.get("room_id") or 0),
                        "poll": updated_poll,
                        "action": "poll_closed",
                        "by_user_id": int(session["user_id"]),
                    },
                    room_id=int(updated_poll.get("room_id") or 0),
                )
            return jsonify({"success": True})
        return jsonify({"error": error or "투표 마감에 실패했습니다."}), 403
