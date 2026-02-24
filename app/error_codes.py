# -*- coding: utf-8 -*-
"""
Error code registry and Korean canonical message mapping.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorSpec:
    code: str
    i18n_key: str


ERROR_MESSAGE_MAP: dict[str, ErrorSpec] = {
    '로그인이 필요합니다.': ErrorSpec('AUTH_LOGIN_REQUIRED', 'errors.auth.login_required'),
    '아이디 또는 비밀번호가 올바르지 않습니다.': ErrorSpec(
        'AUTH_INVALID_CREDENTIALS',
        'errors.auth.invalid_credentials',
    ),
    '아이디와 비밀번호를 입력해주세요.': ErrorSpec('AUTH_MISSING_CREDENTIALS', 'errors.auth.invalid_credentials'),
    'device_token이 필요합니다.': ErrorSpec('AUTH_DEVICE_TOKEN_REQUIRED', 'errors.auth.token_required'),
    '유효하지 않거나 만료된 토큰입니다.': ErrorSpec(
        'AUTH_TOKEN_INVALID_OR_EXPIRED',
        'errors.auth.token_invalid_or_expired',
    ),
    '사용자를 찾을 수 없습니다.': ErrorSpec('USER_NOT_FOUND', 'errors.auth.user_not_found'),
    '대화방 접근 권한이 없습니다.': ErrorSpec('ROOM_ACCESS_DENIED', 'errors.room.access_denied'),
    '대화방을 찾을 수 없습니다.': ErrorSpec('ROOM_NOT_FOUND', 'errors.room.not_found'),
    '관리자 권한이 필요합니다.': ErrorSpec('ROOM_ADMIN_REQUIRED', 'errors.room.admin_required'),
    '잘못된 요청입니다.': ErrorSpec('REQUEST_INVALID', 'errors.request.invalid'),
    '잘못된 요청 형식입니다.': ErrorSpec('REQUEST_INVALID_FORMAT', 'errors.request.invalid_format'),
    '메시지 저장에 실패했습니다.': ErrorSpec('MESSAGE_SAVE_FAILED', 'errors.message.save_failed'),
    '메시지 전송에 실패했습니다.': ErrorSpec('MESSAGE_SEND_FAILED', 'errors.message.send_failed'),
    '메시지 수정에 실패했습니다.': ErrorSpec('MESSAGE_EDIT_FAILED', 'errors.message.edit_failed'),
    '메시지 삭제에 실패했습니다.': ErrorSpec('MESSAGE_DELETE_FAILED', 'errors.message.delete_failed'),
    '업로드 토큰이 필요합니다.': ErrorSpec('UPLOAD_TOKEN_REQUIRED', 'errors.upload.token_required'),
    '업로드 토큰이 이미 사용되었거나 만료되었습니다.': ErrorSpec(
        'UPLOAD_TOKEN_USED_OR_EXPIRED',
        'errors.upload.token_used_or_expired',
    ),
    '파일을 찾을 수 없습니다.': ErrorSpec('FILE_NOT_FOUND', 'errors.file.not_found'),
}


GENERIC_ERROR_SPEC = ErrorSpec('GENERIC_ERROR', 'errors.generic')
