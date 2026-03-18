# -*- coding: utf-8 -*-

from __future__ import annotations

import time
from datetime import datetime

from client.i18n import t
from client.services.api_client import ApiError
from client.services.session_store import StoredSession


class SessionCoordinator:
    def __init__(self, controller) -> None:
        self.controller = controller

    @staticmethod
    def parse_server_ts(raw: object) -> float:
        text = str(raw or "").strip()
        if not text:
            return 0.0
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).timestamp()
            except ValueError:
                continue
        return 0.0

    def update_session_expiry(self, payload: dict) -> None:
        expires_epoch = self.parse_server_ts(payload.get("expires_at"))
        self.controller._session_expires_at_epoch = expires_epoch
        if expires_epoch > 0:
            now = time.time()
            self.controller._session_ttl_seconds = max(0.0, expires_epoch - now)

    def retry_after_unauthorized(self) -> bool:
        return self.refresh_device_session_token(notify=False)

    def refresh_device_session_token(self, *, notify: bool = False) -> bool:
        if self.controller._refresh_inflight:
            return False
        if not self.controller.current_device_token:
            return False
        self.controller._refresh_inflight = True
        try:
            payload = self.controller.api.refresh_device_session(self.controller.current_device_token)
            rotated = str(payload.get("device_token_rotated") or self.controller.current_device_token).strip()
            if not rotated:
                return False
            self.controller.current_device_token = rotated
            self.update_session_expiry(payload)
            if self.controller._remember_device:
                device_name = self.controller.default_device_name()
                stored = self.controller.session_store.load()
                if stored and stored.device_name:
                    device_name = stored.device_name
                self.controller.session_store.save(
                    StoredSession(
                        server_url=self.controller.current_server_url,
                        device_token=self.controller.current_device_token,
                        device_name=device_name,
                    )
                )
            if notify:
                self.controller.main_window.show_info(t("controller.session_refreshed", "Session refreshed."))
            return True
        except Exception:
            return False
        finally:
            self.controller._refresh_inflight = False

    def refresh_device_session_if_needed(self) -> None:
        if not self.controller.current_user:
            return
        if not self.controller.current_device_token:
            return
        if self.controller._session_expires_at_epoch <= 0:
            return
        now = time.time()
        remaining = self.controller._session_expires_at_epoch - now
        threshold = max(
            300.0,
            self.controller._session_ttl_seconds * 0.2 if self.controller._session_ttl_seconds > 0 else 0.0,
        )
        if remaining > threshold:
            return
        self.refresh_device_session_token(notify=False)

    def try_restore_session(self) -> bool:
        stored = self.controller.session_store.load()
        if not stored:
            return False

        try:
            self.controller.api.update_base_url(stored.server_url)
            payload = self.controller.api.refresh_device_session(stored.device_token)
            rotated = payload.get("device_token_rotated") or stored.device_token
            self.on_authenticated(
                payload=payload,
                server_url=stored.server_url,
                remember=True,
                device_name=stored.device_name,
                device_token=rotated,
            )
            return True
        except ApiError as exc:
            if int(getattr(exc, "status_code", 0)) == 401 or getattr(exc, "error_code", "") in (
                "AUTH_TOKEN_INVALID_OR_EXPIRED",
                "AUTH_DEVICE_TOKEN_REQUIRED",
            ):
                self.controller.session_store.clear()
            return False
        except Exception:
            return False

    def on_login_requested(
        self,
        server_url: str,
        username: str,
        password: str,
        device_name: str,
        remember: bool,
    ) -> None:
        self.controller.login_window.set_busy(True)
        try:
            self.controller.api.update_base_url(server_url)
            payload = self.controller.api.create_device_session(
                username=username,
                password=password,
                device_name=device_name,
                remember=remember,
            )
            token = payload.get("device_token", "")
            if not token:
                raise RuntimeError(
                    t(
                        "controller.device_token_missing_in_response",
                        "device_token is missing in login response",
                    )
                )
            self.on_authenticated(
                payload=payload,
                server_url=server_url,
                remember=remember,
                device_name=device_name,
                device_token=token,
            )
        except Exception as exc:
            self.controller.login_window.show_error(str(exc))
        finally:
            self.controller.login_window.set_busy(False)

    def on_register_requested(self, server_url: str, username: str, password: str, nickname: str) -> None:
        self.controller.login_window.set_busy(True)
        try:
            self.controller.api.update_base_url(server_url)
            self.controller.api.register(username=username, password=password, nickname=nickname)
            self.controller.login_window.show_info(t("controller.register_success", "Registered successfully. Please log in."))
        except Exception as exc:
            self.controller.login_window.show_error(str(exc))
        finally:
            self.controller.login_window.set_busy(False)

    def on_authenticated(
        self,
        *,
        payload: dict,
        server_url: str,
        remember: bool,
        device_name: str,
        device_token: str,
    ) -> None:
        self.controller.current_user = payload.get("user") or {}
        self.controller.current_server_url = server_url.rstrip("/")
        self.controller.preferred_server_url = self.controller.current_server_url
        self.controller.current_device_token = device_token
        self.controller._remember_device = bool(remember)
        self.update_session_expiry(payload)
        self.controller.current_room_id = None
        self.controller.current_room_key = ""
        self.controller._message_history_has_more = False
        self.controller._message_history_loading = False
        self.controller._refresh_inflight = False

        if remember:
            self.controller.session_store.save(
                StoredSession(
                    server_url=self.controller.current_server_url,
                    device_token=device_token,
                    device_name=device_name,
                )
            )
        else:
            self.controller.session_store.clear()

        self.controller._restore_pending_sends_from_outbox()
        if self.controller.current_user is None:
            raise RuntimeError("authenticated session is missing user payload")
        self.controller.main_window.set_user(self.controller.current_user)
        self.controller._show_main_window()
        self.controller.login_window.hide()

        try:
            cookie_header = self.controller.api.get_cookie_header()
            self.controller.socket.connect(
                self.controller.current_server_url,
                cookie_header=cookie_header,
                language=self.controller.i18n.display_locale,
            )
        except Exception as exc:
            self.controller.main_window.show_error(
                t("controller.socket_connection_failed", "Socket connection failed: {error}", error=str(exc))
            )

        self.controller._load_rooms()
        self.controller._check_update_policy()
        self.controller._pending_send_timer.start()
        self.controller._session_refresh_timer.start()
        for msg_id, entry in list(self.controller._pending_sends.items()):
            if not entry.get("failed"):
                self.controller._dispatch_pending_send(msg_id)
        self.controller.tray.notify(
            t("app.name", "Intranet Messenger"),
            t("tray.signed_in", "Signed in successfully."),
        )

    def logout(self) -> None:
        self.controller._rooms_reload_timer.stop()
        self.controller._typing_debounce_timer.stop()
        self.controller._search_debounce_timer.stop()
        self.controller._pending_send_timer.stop()
        self.controller._session_refresh_timer.stop()
        try:
            self.controller.socket.disconnect()
        except Exception:
            pass
        try:
            self.controller.api.revoke_current_device_session(self.controller.current_device_token)
        except Exception:
            pass
        try:
            if self.controller.current_user:
                self.controller.outbox_store.clear(
                    user_id=int((self.controller.current_user or {}).get("id") or 0),
                    server_url=self.controller.current_server_url,
                )
        except Exception:
            pass
        self.controller.session_store.clear()
        self.controller.current_user = None
        self.controller.current_room_id = None
        self.controller.current_room_key = ""
        self.controller.current_device_token = ""
        self.controller._visible_rooms_signature = None
        self.controller._last_subscribed_room_ids = ()
        self.controller._clear_remote_search_cache()
        self.controller._remember_device = False
        self.controller._session_expires_at_epoch = 0.0
        self.controller._session_ttl_seconds = 0.0
        self.controller._refresh_inflight = False
        self.controller.current_room_members = []
        self.controller.current_admin_ids = set()
        self.controller.current_is_admin = False
        self.controller._typing_pending = None
        self.controller._typing_sent = False
        self.controller._typing_room_id = None
        self.controller._pending_sends.clear()
        self.controller._failed_send_ids.clear()
        self.controller.main_window.set_delivery_state("idle", 0)
        self.controller.main_window.hide()
        self.controller.polls_dialog.hide()
        self.controller.files_dialog.hide()
        self.controller.admin_dialog.hide()
        self.controller.settings_dialog.hide()
        self.controller.login_window.set_server_url(self.controller.preferred_server_url)
        self.controller.login_window.show()
        self.controller.tray.notify(t("app.name", "Intranet Messenger"), t("tray.signed_out", "Signed out."))

    def quit(self) -> None:
        self.controller._typing_debounce_timer.stop()
        self.controller._search_debounce_timer.stop()
        self.controller._pending_send_timer.stop()
        self.controller._session_refresh_timer.stop()
        try:
            self.controller.socket.disconnect()
        except Exception:
            pass
        self.controller.api.close()
        self.controller.tray.hide()
        self.controller.app.quit()
