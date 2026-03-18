# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from client.i18n import t


class DialogsController:
    def __init__(self, controller) -> None:
        self.controller = controller

    @staticmethod
    def parse_user_ids(raw: str) -> list[int]:
        parsed: list[int] = []
        seen: set[int] = set()
        tokens = re.split(r"[\s,]+", raw.strip())
        for token in tokens:
            if not token:
                continue
            try:
                user_id = int(token)
            except ValueError:
                continue
            if user_id > 0 and user_id not in seen:
                seen.add(user_id)
                parsed.append(user_id)
        return parsed

    def prompt_user_ids(
        self,
        candidates: list[dict[str, Any]],
        *,
        title: str,
        label: str,
        excluded_ids: set[int] | None = None,
    ) -> list[int] | None:
        excluded_ids = excluded_ids or set()
        selectable = []
        for user in candidates:
            try:
                user_id = int(user.get("id") or 0)
            except Exception:
                user_id = 0
            if user_id <= 0 or user_id in excluded_ids:
                continue
            nickname = str(user.get("nickname") or user.get("username") or user_id)
            username = str(user.get("username") or "")
            if username and username != nickname:
                selectable.append(f"{user_id}: {nickname} (@{username})")
            else:
                selectable.append(f"{user_id}: {nickname}")

        if not selectable:
            self.controller.main_window.show_info(t("controller.no_selectable_users", "No selectable users found."))
            return None

        preview = "\n".join(selectable[:30])
        if len(selectable) > 30:
            preview += "\n..."
        prompt = (
            f"{label}\n\n"
            f"{t('controller.user_picker_help', 'Enter IDs separated by comma or whitespace.')}\n\n"
            f"{preview}"
        )
        raw_text, ok = QInputDialog.getMultiLineText(self.controller.main_window, title, prompt)
        if not ok:
            return None
        user_ids = self.parse_user_ids(raw_text)
        if not user_ids:
            self.controller.main_window.show_info(t("controller.user_picker_empty", "No valid user IDs were entered."))
            return None
        return user_ids

    def create_room(self) -> None:
        try:
            users = self.controller.api.get_users()
            selected_user_ids = self.prompt_user_ids(
                users,
                title=t("main.new_room", "New Room"),
                label=t("controller.select_members_for_room", "Select users to create a new conversation."),
            )
            if selected_user_ids is None:
                return

            room_name, ok = QInputDialog.getText(
                self.controller.main_window,
                t("main.new_room", "New Room"),
                t("controller.room_name_optional", "Room name (optional)"),
            )
            if not ok:
                return

            created = self.controller.api.create_room(selected_user_ids, room_name.strip())
            room_id = int(created.get("room_id") or 0)
            self.controller._load_rooms()
            if room_id > 0:
                self.controller.main_window.select_room(room_id)
        except Exception as exc:
            self.controller.main_window.show_error(str(exc))

    def invite_members(self) -> None:
        room_id = self.controller._require_room()
        if not room_id:
            return
        try:
            all_users = self.controller.api.get_users()
            room_info = self.controller.api.get_room_info(room_id)
            current_member_ids = {
                int(member.get("id") or 0)
                for member in (room_info.get("members") or [])
                if int(member.get("id") or 0) > 0
            }
            selected_user_ids = self.prompt_user_ids(
                all_users,
                title=t("main.invite_members", "Invite Members"),
                label=t("controller.select_members_to_invite", "Select users to invite to this room."),
                excluded_ids=current_member_ids,
            )
            if selected_user_ids is None:
                return
            result = self.controller.api.invite_room_members(room_id, selected_user_ids)
            added = int(result.get("added_count") or 0)
            self.controller.main_window.show_info(
                t("controller.members_invited", "{count} members invited.", count=added)
            )
            self.controller._reload_current_room_messages(refresh_admins=True)
            self.controller._schedule_rooms_reload(120)
        except Exception as exc:
            self.controller.main_window.show_error(str(exc))

    def leave_room(self) -> None:
        room_id = self.controller._require_room()
        if not room_id:
            return
        confirmed = QMessageBox.question(
            self.controller.main_window,
            t("main.leave_room", "Leave Room"),
            t("controller.leave_room_confirm", "Do you want to leave this room?"),
        )
        if confirmed != QMessageBox.StandardButton.Yes:
            return
        try:
            self.controller.api.leave_room(room_id)
            self.controller.socket.leave_room(room_id)
            self.controller.current_room_id = None
            self.controller.current_room_key = ""
            self.controller.current_room_members = []
            self.controller.current_admin_ids = set()
            self.controller.current_is_admin = False
            self.controller._typing_pending = False
            self.controller._typing_sent = False
            self.controller._typing_room_id = None
            self.controller.main_window.clear_room_selection()
            self.controller._load_rooms()
        except Exception as exc:
            self.controller.main_window.show_error(str(exc))

    def rename_room(self) -> None:
        room_id = self.controller._require_room()
        if not room_id:
            return
        try:
            if not self.controller.api.is_room_admin(room_id):
                self.controller.main_window.show_error(t("controller.admin_required", "Administrator privilege is required."))
                return
            current_name = next(
                (str(room.get("name") or "") for room in self.controller.rooms_cache if int(room.get("id") or 0) == room_id),
                "",
            )
            new_name, ok = QInputDialog.getText(
                self.controller.main_window,
                t("main.rename_room", "Rename Room"),
                t("controller.new_room_name", "New room name"),
                text=current_name,
            )
            if not ok:
                return
            normalized = new_name.strip()
            if not normalized:
                self.controller.main_window.show_info(t("controller.room_name_required", "Room name is required."))
                return
            self.controller.api.update_room_name(room_id, normalized)
            self.controller._update_room_cache_name(room_id, normalized)
            self.controller.main_window.set_room_title(normalized)
            self.controller._set_rooms_view(self.controller.rooms_cache)
        except Exception as exc:
            self.controller.main_window.show_error(str(exc))

    def edit_profile(self) -> None:
        try:
            profile = self.controller.api.get_profile()
            nickname_default = str(
                profile.get("nickname")
                or (self.controller.current_user or {}).get("nickname")
                or (self.controller.current_user or {}).get("username")
                or ""
            )
            status_default = str(profile.get("status_message") or "")
            nickname, ok = QInputDialog.getText(
                self.controller.main_window,
                t("main.edit_profile", "Edit Profile"),
                t("controller.profile_nickname", "Nickname"),
                text=nickname_default,
            )
            if not ok:
                return
            normalized_nickname = nickname.strip()
            if not normalized_nickname:
                self.controller.main_window.show_info(t("controller.nickname_required", "Nickname is required."))
                return

            status, ok = QInputDialog.getText(
                self.controller.main_window,
                t("main.edit_profile", "Edit Profile"),
                t("controller.profile_status_message", "Status message"),
                text=status_default,
            )
            if not ok:
                return

            self.controller.api.update_profile(normalized_nickname, status.strip())
            if self.controller.current_user is None:
                self.controller.current_user = {}
            self.controller.current_user["nickname"] = normalized_nickname
            self.controller.current_user["status_message"] = status.strip()
            self.controller.main_window.set_user(self.controller.current_user)
        except Exception as exc:
            self.controller.main_window.show_error(str(exc))

    def open_settings(self) -> None:
        self.controller.settings_dialog.set_values(
            server_url=self.controller.preferred_server_url,
            startup_enabled=self.controller.startup_manager.is_enabled(),
            minimize_to_tray=self.controller.main_window.minimize_to_tray,
            language_preference=self.controller.i18n.preference,
            update_channel=str(self.controller._settings.value("updates/channel", "stable", type=str) or "stable"),
        )
        self.controller.settings_dialog.show()
        self.controller.settings_dialog.activateWindow()
        self.controller.settings_dialog.raise_()

    def on_settings_saved(
        self,
        server_url: str,
        startup_enabled: bool,
        minimize_to_tray: bool,
        language_preference: str,
        update_channel: str,
    ) -> None:
        try:
            self.controller.startup_manager.set_enabled(startup_enabled)
        except Exception as exc:
            self.controller.main_window.show_error(
                t("settings.startup_update_failed", "Failed to update startup setting: {error}", error=str(exc))
            )
            return

        self.controller.main_window.minimize_to_tray = minimize_to_tray
        if server_url:
            normalized = server_url.rstrip("/")
            self.controller.preferred_server_url = normalized
            self.controller.login_window.set_server_url(normalized)
            if normalized != self.controller.current_server_url.rstrip("/"):
                self.controller.main_window.show_info(
                    t("settings.server_applied_next_login", "Server URL updated. It will be applied on next login.")
                )
        self.controller.i18n.set_preference(language_preference or "auto")
        normalized_channel = (update_channel or "stable").strip().lower()
        if normalized_channel not in ("stable", "canary"):
            normalized_channel = "stable"
        self.controller._settings.setValue("updates/channel", normalized_channel)
        self.controller.settings_dialog.hide()
        self.controller.main_window.show_info(t("settings.saved", "Settings saved."))

    def open_polls(self) -> None:
        room_id = self.controller._require_room()
        if not room_id:
            return
        self.controller.polls_dialog.show()
        self.controller.polls_dialog.activateWindow()
        self.controller.polls_dialog.raise_()
        self.controller._refresh_polls()

    def open_files(self) -> None:
        room_id = self.controller._require_room()
        if not room_id:
            return
        self.controller.files_dialog.show()
        self.controller.files_dialog.activateWindow()
        self.controller.files_dialog.raise_()
        self.controller._refresh_files()

    def download_room_file(self, file_info: dict[str, Any]) -> None:
        file_path = str(file_info.get("file_path") or "")
        file_name = str(file_info.get("file_name") or Path(file_path).name or "download.bin")
        if not file_path:
            self.controller.main_window.show_error(t("controller.invalid_file_metadata", "Invalid file metadata."))
            return
        target, _ = QFileDialog.getSaveFileName(
            self.controller.main_window,
            t("main.save_file", "Save File"),
            file_name,
        )
        if not target:
            return
        try:
            saved = self.controller.api.download_upload_file(file_path, target)
            self.controller.main_window.show_info(t("main.saved", "Saved: {path}", path=saved))
        except Exception as exc:
            self.controller.main_window.show_error(str(exc))

    def delete_room_file(self, file_id: int) -> None:
        room_id = self.controller._require_room()
        if not room_id:
            return
        try:
            self.controller.api.delete_room_file(room_id, file_id)
            self.controller._refresh_files()
        except Exception as exc:
            self.controller.main_window.show_error(str(exc))

    def open_admin(self) -> None:
        room_id = self.controller._require_room()
        if not room_id:
            return
        self.controller.admin_dialog.show()
        self.controller.admin_dialog.activateWindow()
        self.controller.admin_dialog.raise_()
        self.controller._refresh_admins()
