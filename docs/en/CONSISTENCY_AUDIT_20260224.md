[Korean version](../ko/CONSISTENCY_AUDIT_20260224.md)

# Doc-Code Consistency Audit (2026-02-24)

## 1. Scope

- Documents:
  - `README.md`, `README.en.md`
  - `TRANSITION_CHECKLIST.md`
  - `REAL_MESSENGER_IMPLEMENTATION_REVIEW_20260224.md`
  - `docs/ARCHITECTURE.md`, `docs/API_SOCKET_CONTRACT.md`
  - indexes/contracts/architecture under `docs/ko/*`, `docs/en/*`
- Code:
  - Server: `app/routes.py`, `app/sockets.py`, `app/models/messages.py`, `config.py`
  - Client: `client/app_controller.py`, `client/ui/main_window.py`, `client/ui/settings_dialog.py`, `client/services/socket_client.py`, `client/services/session_store.py`

## 2. Mismatch Items and Applied Updates

1. Socket security/integrity
- Mismatch: docs still described these as pending while code was updated.
- Applied:
  - reject unauthenticated socket connection (`connect -> return False`)
  - block cross-room `reply_to`
  - validate message-room consistency for `message_read`
  - enforce same-room reply join in message queries

2. REST -> Socket realtime sync
- Mismatch: realtime bridge behavior not clearly reflected in docs.
- Applied:
  - room create/invite/leave/kick/rename
  - pin create/delete
  - poll create/vote/close
  - admin role update
  - canonical socket events emitted on REST success paths

3. Desktop feature parity
- Mismatch: checklists were ahead of documented UI wiring state.
- Applied:
  - UI wiring for create room/invite/rename/leave/edit profile
  - typing outbound with 500ms debounce
  - pending/failed/retry send UX with socket ACK
  - update channel (`stable`/`canary`) selection in settings

4. Session store and secure defaults
- Applied:
  - fallback file read when keyring value is empty
  - clear both keyring and fallback file
  - `USE_HTTPS` default moved to env-based production-safe logic (`MESSENGER_ENV`, `USE_HTTPS`)

## 3. Contract Documentation Additions

- API error metadata fields:
  - `error`, `error_code`, `error_localized`, `locale`
- Socket error metadata fields:
  - `message`, `message_code`, `message_localized`, `locale`
- `send_message` ACK contract:
  - success: `{ ok: true, message_id }`
  - failure: `{ ok: false, error }`
- `client_msg_id` roundtrip contract:
  - client may send `client_msg_id` in `send_message`
  - server reflects it in `new_message` payload

## 4. Validation

- Full test suite:
  - `pytest tests -q` passed (`99 passed`)
- New regression tests:
  - `tests/test_socket_security_regressions.py`
  - `tests/test_session_store_fallback.py`

## 5. Operational Follow-up

1. Release-time checks
- update test counts and status wording in docs at release time
- keep ko/en docs in sync whenever contract changes

2. Suggested automation
- add CI check for doc link integrity and key API/socket contract snapshots
