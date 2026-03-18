# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
from bisect import bisect_left
from typing import Any

from flask import jsonify, request, session

from app.extensions import limiter
from app.http.common import emit_socket_event, json_dict, normalize_date_bounds, parse_optional_positive_int
from app.models import (
    advanced_search as model_advanced_search,
    delete_message,
    edit_message,
    get_message_reactions,
    get_message_room_id,
    get_pinned_messages,
    get_room_key,
    get_room_last_reads,
    get_room_members,
    get_room_messages,
    is_room_member,
    pin_message,
    toggle_reaction,
    unpin_message,
)
from app.utils import sanitize_input

logger = logging.getLogger(__name__)


def _advanced_search_impl():
    try:
        import app.routes as routes

        return getattr(routes, "advanced_search", model_advanced_search)
    except Exception:
        return model_advanced_search


def register_message_routes(app) -> None:
    @app.route("/api/rooms/<int:room_id>/messages")
    def get_messages(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "대화방 접근 권한이 없습니다."}), 403

        try:
            before_id = request.args.get("before_id", type=int)
            limit = min(max(request.args.get("limit", type=int) or 50, 1), 200)
            include_meta = str(request.args.get("include_meta", "1")).lower() in ("1", "true", "yes")

            messages = get_room_messages(room_id, before_id=before_id, limit=limit)
            members = get_room_members(room_id) if include_meta else None
            encryption_key = get_room_key(room_id) if include_meta else None

            if messages:
                if include_meta and members:
                    user_last_read: dict[Any, int] = {}
                    last_read_ids: list[int] = []
                    for member in members:
                        try:
                            uid = member.get("id")
                            value = member.get("last_read_message_id") or 0
                        except Exception:
                            continue
                        if uid is None:
                            continue
                        user_last_read[uid] = value
                        last_read_ids.append(value)
                else:
                    last_reads = get_room_last_reads(room_id)
                    user_last_read = {}
                    last_read_ids = []
                    for last_read, uid in last_reads:
                        value = last_read or 0
                        user_last_read[uid] = value
                        last_read_ids.append(value)
                last_read_ids.sort()

                for message in messages:
                    sender_id = message["sender_id"]
                    message_id = message["id"]
                    unread = bisect_left(last_read_ids, message_id)
                    sender_last_read = user_last_read.get(sender_id, 0)
                    if sender_last_read < message_id:
                        unread -= 1
                    message["unread_count"] = max(unread, 0)

            response: dict[str, Any] = {"messages": messages}
            if include_meta:
                response["members"] = members
                response["encryption_key"] = encryption_key
            return jsonify(response)
        except Exception as exc:
            logger.error(f"메시지 로드 오류: {exc}")
            return jsonify({"error": "메시지 로드 실패"}), 500

    @app.route("/api/messages/<int:message_id>", methods=["DELETE"])
    def delete_message_route(message_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        success, result = delete_message(message_id, session["user_id"])
        if success:
            return jsonify({"success": True, "room_id": result})
        return jsonify({"error": result}), 403

    @app.route("/api/messages/<int:message_id>", methods=["PUT"])
    def edit_message_route(message_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        data = json_dict()
        new_content = data.get("content", "")
        if not new_content:
            return jsonify({"error": "메시지 내용을 입력해주세요."}), 400

        success, error, room_id = edit_message(message_id, session["user_id"], new_content)
        if success:
            return jsonify({"success": True, "room_id": room_id})
        return jsonify({"error": error}), 403

    @app.route("/api/search")
    @limiter.limit("30 per minute")
    def search():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401

        query = request.args.get("q")
        raw_date_from = request.args.get("date_from")
        raw_date_to = request.args.get("date_to")
        file_only = str(request.args.get("file_only", "")).lower() in ("1", "true", "yes")
        room_id = request.args.get("room_id", type=int)
        offset = max(request.args.get("offset", type=int) or 0, 0)
        limit = min(max(request.args.get("limit", type=int) or 50, 1), 200)

        if (not query or not query.strip()) and not raw_date_from and not raw_date_to and not file_only:
            return jsonify([])
        normalized_query = (query or "").strip()
        if normalized_query and len(normalized_query) < 2:
            return jsonify([])

        try:
            date_from, date_to = normalize_date_bounds(raw_date_from, raw_date_to)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        results = _advanced_search_impl()(
            user_id=session["user_id"],
            query=(normalized_query or None),
            room_id=room_id,
            date_from=(date_from or None),
            date_to=(date_to or None),
            file_only=file_only,
            limit=limit,
            offset=offset,
        )
        return jsonify(results.get("messages", []))

    @app.route("/api/rooms/<int:room_id>/pins")
    def get_room_pins(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "접근 권한이 없습니다."}), 403
        return jsonify(get_pinned_messages(room_id))

    @app.route("/api/rooms/<int:room_id>/pins", methods=["POST"])
    def create_pin(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "접근 권한이 없습니다."}), 403

        data = json_dict()
        message_id = data.get("message_id")
        content = sanitize_input(data.get("content", ""), max_length=500)
        if not message_id and not content:
            return jsonify({"error": "고정할 메시지 또는 내용을 입력해주세요."}), 400

        normalized_message_id: int | None
        if message_id is None or message_id == "":
            normalized_message_id = None
        else:
            try:
                normalized_message_id = int(message_id)
            except (TypeError, ValueError):
                return jsonify({"error": "message_id는 정수여야 합니다."}), 400

        pin_id = pin_message(room_id, session["user_id"], normalized_message_id, content)
        if pin_id:
            emit_socket_event(
                "pin_updated",
                {"room_id": room_id, "pin_id": pin_id, "action": "pin_created", "by_user_id": int(session["user_id"])},
                room_id=room_id,
            )
            return jsonify({"success": True, "pin_id": pin_id})
        return jsonify({"error": "공지 고정에 실패했습니다."}), 500

    @app.route("/api/rooms/<int:room_id>/pins/<int:pin_id>", methods=["DELETE"])
    def delete_pin(room_id, pin_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "접근 권한이 없습니다."}), 403

        success, error = unpin_message(pin_id, session["user_id"], room_id)
        if success:
            emit_socket_event(
                "pin_updated",
                {"room_id": room_id, "pin_id": pin_id, "action": "pin_deleted", "by_user_id": int(session["user_id"])},
                room_id=room_id,
            )
            return jsonify({"success": True})
        if error == "공지를 찾을 수 없습니다.":
            return jsonify({"error": error}), 404
        if error == "요청한 대화방과 공지의 대화방이 일치하지 않습니다.":
            return jsonify({"error": error}), 403
        return jsonify({"error": error or "공지 해제에 실패했습니다."}), 400

    @app.route("/api/messages/<int:message_id>/reactions")
    def get_reactions(message_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        room_id = get_message_room_id(message_id)
        if room_id is None or not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "대화방 접근 권한이 없습니다."}), 403
        return jsonify(get_message_reactions(message_id))

    @app.route("/api/messages/<int:message_id>/reactions", methods=["POST"])
    def add_reaction_route(message_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        room_id = get_message_room_id(message_id)
        if room_id is None or not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "대화방 접근 권한이 없습니다."}), 403

        data = json_dict()
        emoji = data.get("emoji", "")
        if not emoji or len(emoji) > 10:
            return jsonify({"error": "유효하지 않은 이모지입니다."}), 400

        success, action = toggle_reaction(message_id, session["user_id"], emoji)
        if success:
            reactions = get_message_reactions(message_id)
            return jsonify({"success": True, "action": action, "reactions": reactions})
        return jsonify({"error": "리액션 추가에 실패했습니다."}), 500

    @app.route("/api/search/advanced", methods=["POST"])
    @limiter.limit("30 per minute")
    def advanced_search_route():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401

        data = json_dict()
        query = data.get("query")
        if query is None:
            normalized_query = None
        elif isinstance(query, str):
            normalized_query = query.strip()
            if len(normalized_query) > 200:
                return jsonify({"error": "query 길이가 너무 깁니다."}), 400
            if not normalized_query:
                normalized_query = None
        else:
            return jsonify({"error": "query는 문자열이어야 합니다."}), 400

        try:
            room_id = parse_optional_positive_int(data, "room_id")
            sender_id = parse_optional_positive_int(data, "sender_id")
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        try:
            date_from, date_to = normalize_date_bounds(data.get("date_from"), data.get("date_to"))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        raw_file_only = data.get("file_only", False)
        if isinstance(raw_file_only, bool):
            file_only = raw_file_only
        elif isinstance(raw_file_only, str):
            normalized_bool = raw_file_only.strip().lower()
            if normalized_bool in ("1", "true", "yes", "on"):
                file_only = True
            elif normalized_bool in ("0", "false", "no", "off", ""):
                file_only = False
            else:
                return jsonify({"error": "file_only는 boolean 값이어야 합니다."}), 400
        else:
            return jsonify({"error": "file_only는 boolean 값이어야 합니다."}), 400

        raw_limit = data.get("limit", 50)
        raw_offset = data.get("offset", 0)
        try:
            limit = int(raw_limit)
            offset = int(raw_offset)
        except (TypeError, ValueError):
            return jsonify({"error": "limit/offset은 정수여야 합니다."}), 400
        limit = min(max(limit, 1), 200)
        offset = max(offset, 0)

        results = _advanced_search_impl()(
            user_id=session["user_id"],
            query=normalized_query,
            room_id=room_id,
            sender_id=sender_id,
            date_from=date_from,
            date_to=date_to,
            file_only=file_only,
            limit=limit,
            offset=offset,
        )
        return jsonify(results)
