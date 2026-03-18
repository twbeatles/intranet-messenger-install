# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
from typing import Any

from flask import jsonify, request, session

from app.http.common import emit_socket_event, force_unsubscribe_user_from_room, json_dict
from app.models import (
    add_room_member,
    create_room,
    get_all_users,
    get_online_users,
    get_room_admins,
    get_room_by_id,
    get_room_members,
    get_user_by_id,
    get_user_rooms,
    is_room_admin,
    is_room_member,
    leave_room_db,
    mute_room,
    pin_room,
    set_room_admin,
    update_room_name,
)
from app.utils import sanitize_input

logger = logging.getLogger(__name__)


def register_room_routes(app) -> None:
    @app.route("/api/users")
    def get_users():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        users = get_all_users()
        return jsonify([user for user in users if user["id"] != session["user_id"]])

    @app.route("/api/users/online")
    def get_online_users_route():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        users = get_online_users()
        users = [user for user in users if user["id"] != session["user_id"]]
        return jsonify(users)

    @app.route("/api/rooms")
    def get_rooms():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        include_members = str(request.args.get("include_members", "")).lower() in ("1", "true", "yes")
        rooms = get_user_rooms(session["user_id"], include_members=include_members)
        return jsonify(rooms)

    @app.route("/api/rooms", methods=["POST"])
    def create_room_route():
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401

        data = json_dict()
        if not isinstance(data, dict):
            return jsonify({"error": "잘못된 요청 형식입니다."}), 400
        has_members = "members" in data
        has_member_ids = "member_ids" in data
        if has_members:
            raw_members = data.get("members")
            if has_member_ids:
                logger.warning("Both members and member_ids were provided; members will be used.")
        else:
            raw_members = data.get("member_ids", [])

        if raw_members is None:
            raw_members = []
        if not isinstance(raw_members, list):
            return jsonify({"error": "members 또는 member_ids는 배열이어야 합니다."}), 400

        normalized_members: list[int] = []
        seen: set[int] = set()
        for value in raw_members:
            try:
                member_id = int(value)
            except (TypeError, ValueError):
                return jsonify({"error": "멤버 ID는 정수여야 합니다."}), 400
            if member_id <= 0 or member_id in seen:
                continue
            seen.add(member_id)
            normalized_members.append(member_id)

        if session["user_id"] not in seen:
            normalized_members.append(session["user_id"])
            seen.add(session["user_id"])

        member_ids = [uid for uid in normalized_members if get_user_by_id(uid)]
        if session["user_id"] not in member_ids:
            member_ids.append(session["user_id"])

        room_type = "direct" if len(member_ids) == 2 else "group"
        name = data.get("name", "")

        try:
            room_id = create_room(name, room_type, session["user_id"], member_ids)
            emit_socket_event(
                "room_updated",
                {"room_id": room_id, "action": "room_created", "by_user_id": int(session["user_id"])},
                user_ids=[int(uid) for uid in member_ids],
            )
            return jsonify({"success": True, "room_id": room_id})
        except Exception as exc:
            logger.error(f"Room creation failed: {exc}")
            return jsonify({"error": "대화방 생성에 실패했습니다."}), 500

    @app.route("/api/rooms/<int:room_id>/members", methods=["POST"])
    def invite_member(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "대화방 접근 권한이 없습니다."}), 403

        data = json_dict()
        user_ids = data.get("user_ids", [])
        user_id = data.get("user_id")
        if user_id:
            user_ids = [user_id]

        valid_user_ids = [uid for uid in user_ids if get_user_by_id(uid)]
        added = 0
        added_user_ids: list[int] = []
        for uid in valid_user_ids:
            if add_room_member(room_id, uid):
                added += 1
                added_user_ids.append(int(uid))

        if added > 0:
            emit_socket_event(
                "room_members_updated",
                {
                    "room_id": room_id,
                    "action": "members_invited",
                    "by_user_id": int(session["user_id"]),
                    "added_count": added,
                },
                room_id=room_id,
            )
            emit_socket_event(
                "room_updated",
                {
                    "room_id": room_id,
                    "action": "members_invited",
                    "by_user_id": int(session["user_id"]),
                },
                room_id=room_id,
                user_ids=added_user_ids,
            )
            return jsonify({"success": True, "added_count": added})
        return jsonify({"error": "이미 참여중인 사용자입니다."}), 400

    @app.route("/api/rooms/<int:room_id>/leave", methods=["POST"])
    def leave_room_route(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "대화방 접근 권한이 없습니다."}), 403

        left_user_id = int(session["user_id"])
        success = leave_room_db(room_id, left_user_id)
        if not success:
            return jsonify({"error": "대화방 나가기에 실패했습니다."}), 400
        force_unsubscribe_user_from_room(left_user_id, room_id)
        emit_socket_event(
            "room_members_updated",
            {"room_id": room_id, "action": "member_left", "user_id": left_user_id, "by_user_id": left_user_id},
            room_id=room_id,
            user_ids=[left_user_id],
        )
        emit_socket_event(
            "room_updated",
            {"room_id": room_id, "action": "member_left", "user_id": left_user_id},
            room_id=room_id,
            user_ids=[left_user_id],
        )
        return jsonify({"success": True})

    @app.route("/api/rooms/<int:room_id>/members/<int:target_user_id>", methods=["DELETE"])
    def kick_member(room_id, target_user_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "대화방 접근 권한이 없습니다."}), 403
        if not is_room_admin(room_id, session["user_id"]):
            return jsonify({"error": "관리자만 멤버를 퇴장시킬 수 있습니다."}), 403
        if target_user_id == session["user_id"]:
            return jsonify({"error": "자신을 퇴장시킬 수 없습니다."}), 400
        if is_room_admin(room_id, target_user_id):
            return jsonify({"error": "관리자는 강퇴할 수 없습니다."}), 403
        if not is_room_member(room_id, target_user_id):
            return jsonify({"error": "해당 사용자는 대화방 멤버가 아닙니다."}), 400

        success = leave_room_db(room_id, target_user_id)
        if not success:
            return jsonify({"error": "강퇴 처리에 실패했습니다."}), 400
        force_unsubscribe_user_from_room(int(target_user_id), room_id)

        actor_id = int(session["user_id"])
        emit_socket_event(
            "room_members_updated",
            {"room_id": room_id, "action": "member_kicked", "user_id": int(target_user_id), "by_user_id": actor_id},
            room_id=room_id,
            user_ids=[int(target_user_id)],
        )
        emit_socket_event(
            "room_updated",
            {"room_id": room_id, "action": "member_kicked", "user_id": int(target_user_id), "by_user_id": actor_id},
            room_id=room_id,
            user_ids=[int(target_user_id)],
        )
        return jsonify({"success": True})

    @app.route("/api/rooms/<int:room_id>/name", methods=["PUT"])
    def update_room_name_route(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "대화방 접근 권한이 없습니다."}), 403
        if not is_room_admin(room_id, session["user_id"]):
            return jsonify({"error": "관리자만 대화방 이름을 변경할 수 있습니다."}), 403

        data = json_dict()
        new_name = sanitize_input(data.get("name", ""), max_length=50)
        if not new_name:
            return jsonify({"error": "대화방 이름을 입력해주세요."}), 400

        update_room_name(room_id, new_name)
        emit_socket_event(
            "room_name_updated",
            {"room_id": room_id, "name": new_name, "by_user_id": int(session["user_id"])},
            room_id=room_id,
        )
        emit_socket_event(
            "room_updated",
            {"room_id": room_id, "action": "room_renamed", "name": new_name, "by_user_id": int(session["user_id"])},
            room_id=room_id,
        )
        return jsonify({"success": True})

    @app.route("/api/rooms/<int:room_id>/pin-room", methods=["POST"])
    @app.route("/api/rooms/<int:room_id>/pin", methods=["POST"])
    def pin_room_route(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "대화방 접근 권한이 없습니다."}), 403

        data = json_dict()
        pinned = data.get("pinned", True)
        if pin_room(session["user_id"], room_id, pinned):
            return jsonify({"success": True})
        return jsonify({"error": "설정 변경에 실패했습니다."}), 400

    @app.route("/api/rooms/<int:room_id>/mute", methods=["POST"])
    def mute_room_route(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "대화방 접근 권한이 없습니다."}), 403

        data = json_dict()
        muted = data.get("muted", True)
        if mute_room(session["user_id"], room_id, muted):
            return jsonify({"success": True})
        return jsonify({"error": "설정 변경에 실패했습니다."}), 400

    @app.route("/api/rooms/<int:room_id>/info")
    def get_room_info(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "대화방 접근 권한이 없습니다."}), 403

        room = get_room_by_id(room_id)
        if not room:
            return jsonify({"error": "대화방을 찾을 수 없습니다."}), 404
        members = get_room_members(room_id)
        room["members"] = members
        room.pop("encryption_key", None)
        return jsonify(room)

    @app.route("/api/rooms/<int:room_id>/admins")
    def get_admins(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "접근 권한이 없습니다."}), 403
        admins = get_room_admins(room_id)
        return jsonify(admins)

    @app.route("/api/rooms/<int:room_id>/admins", methods=["POST"])
    def set_admin_route(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "접근 권한이 없습니다."}), 403
        if not is_room_admin(room_id, session["user_id"]):
            return jsonify({"error": "관리자 권한이 필요합니다."}), 403

        data = json_dict()
        target_user_id = data.get("user_id")
        if not isinstance(data.get("is_admin", True), bool):
            return jsonify({"error": "is_admin은 boolean 값이어야 합니다."}), 400
        is_admin = bool(data.get("is_admin", True))

        if target_user_id is None:
            return jsonify({"error": "사용자를 선택해주세요."}), 400
        try:
            target_user_id = int(target_user_id)
        except (TypeError, ValueError):
            return jsonify({"error": "유효한 사용자 ID가 필요합니다."}), 400
        if target_user_id <= 0:
            return jsonify({"error": "유효한 사용자 ID가 필요합니다."}), 400
        if not is_room_member(room_id, target_user_id):
            return jsonify({"error": "해당 사용자는 대화방 멤버가 아닙니다."}), 400

        if not is_admin:
            admins = get_room_admins(room_id)
            if len(admins) <= 1:
                return jsonify({"error": "최소 한 명의 관리자가 필요합니다."}), 400

        if set_room_admin(room_id, target_user_id, is_admin):
            emit_socket_event(
                "admin_updated",
                {
                    "room_id": room_id,
                    "user_id": int(target_user_id),
                    "is_admin": bool(is_admin),
                    "by_user_id": int(session["user_id"]),
                },
                room_id=room_id,
            )
            emit_socket_event(
                "room_members_updated",
                {
                    "room_id": room_id,
                    "action": "admin_updated",
                    "user_id": int(target_user_id),
                    "is_admin": bool(is_admin),
                    "by_user_id": int(session["user_id"]),
                },
                room_id=room_id,
            )
            return jsonify({"success": True})
        return jsonify({"error": "관리자 설정에 실패했습니다."}), 500

    @app.route("/api/rooms/<int:room_id>/admin-check")
    def check_admin(room_id):
        if "user_id" not in session:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if not is_room_member(room_id, session["user_id"]):
            return jsonify({"error": "접근 권한이 없습니다."}), 403
        return jsonify({"is_admin": is_room_admin(room_id, session["user_id"])})
