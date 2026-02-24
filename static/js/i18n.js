/**
 * Web i18n runtime (ko default, en support)
 */

(function () {
    var SUPPORTED = ['ko', 'en'];
    var DEFAULT_LOCALE = 'ko';
    var STORAGE_KEY = 'app.language'; // auto | ko | en

    var preference = 'auto';
    var locale = DEFAULT_LOCALE;
    var catalog = {};

    var BUILTIN = {
        ko: {
            'app.page_title': '🔒 사내 메신저 (E2E 암호화)',
            'app.title': '🔒 사내 메신저',
            'app.subtitle': '종단간 암호화로 안전하게 소통하세요',
            'app.encryption_badge': '🔒 E2E 암호화 적용',
            'app.welcome': '{nickname}님 환영합니다!',
            'auth.username': '아이디',
            'auth.password': '비밀번호',
            'auth.nickname': '닉네임',
            'auth.login': '로그인',
            'auth.register': '회원가입',
            'auth.no_account': '계정이 없으신가요?',
            'auth.have_account': '이미 계정이 있으신가요?',
            'auth.login.required': '아이디와 비밀번호를 입력하세요.',
            'auth.login.success': '로그인 성공!',
            'auth.login.failed': '로그인 실패',
            'auth.register.success': '회원가입 완료! 로그인해주세요.',
            'auth.register.failed': '회원가입 실패',
            'auth.server_error': '서버 연결 오류',
            'auth.session_required': '세션 체크 실패, 로그인 필요',
            'main.conversations': '🔒 대화',
            'main.search_placeholder': '대화 검색...',
            'main.select_room': '대화를 선택하세요',
            'main.select_room_desc': '왼쪽에서 대화를 선택하거나\\n새 대화를 시작하세요',
            'main.new_chat': '➕ 새 대화 시작',
            'main.status.online': '온라인',
            'main.shortcut.new_chat': '으로 빠르게 시작',
            'main.room.pin': '상단 고정',
            'main.room.unpin': '고정 해제',
            'main.room.mute': '알림 끄기',
            'main.room.unmute': '알림 켜기',
            'main.connection.connecting': '연결 중...',
            'socket.connected': '연결됨',
            'socket.disconnected': '연결 끊김',
            'socket.reconnecting': '재연결 중... ({attempt})',
            'settings.title': '🎨 화면 설정',
            'settings.language': '언어',
            'settings.default': '기본값',
            'common.close': '닫기',
            'common.save': '저장',
            'common.cancel': '취소',
            'common.search': '검색',
            'language.auto': '자동',
            'language.ko': '한국어',
            'language.en': 'English',
            'errors.generic': '요청 처리 중 오류가 발생했습니다.',
            'errors.network': '서버 연결 오류',
            'profile.edit': '⚙ 프로필 수정',
            'profile.image.alt': '프로필',
            'feature.poll.create': '투표가 생성되었습니다.',
            'feature.poll.create_failed': '투표 생성에 실패했습니다.',
            'feature.poll.close_confirm': '이 투표를 종료하시겠습니까?',
            'feature.file.delete_confirm': '이 파일을 삭제하시겠습니까?',
            'feature.file.deleted': '파일이 삭제되었습니다.',
            'feature.file.delete_failed': '파일 삭제에 실패했습니다.',
            'feature.pinned': '공지로 고정되었습니다.',
            'feature.unpinned': '공지가 삭제되었습니다.',
            'feature.admin.updated': '관리자 설정이 적용되었습니다.',
            'feature.search.no_result': '검색 결과가 없습니다',
            'notify.new_message': '새 메시지',
            'notify.mention_title': '멘션됨 - {sender}',
            'notify.unsupported': '이 브라우저는 알림을 지원하지 않습니다.',
            'message.unread_divider': '여기서부터 읽지 않음',
            'message.all_read': '모두 읽음',
            'message.unread_count': '{count}명 안읽음',
            'message.decrypting': '[복호화 중...]',
            'message.encrypted': '[암호화된 메시지]',
            'message.reply': '답장',
            'message.reaction': '리액션',
            'message.edit': '수정',
            'message.delete': '삭제',
            'message.file_invalid_path': '[잘못된 이미지 경로]',
            'message.sender.unknown': '사용자',
            'message.reply_from': '↩ {sender}님의 메시지'
        },
        en: {
            'app.page_title': '🔒 Intranet Messenger (E2E Encrypted)',
            'app.title': '🔒 Intranet Messenger',
            'app.subtitle': 'Communicate safely with end-to-end encryption',
            'app.encryption_badge': '🔒 E2E Encryption Enabled',
            'app.welcome': 'Welcome, {nickname}!',
            'auth.username': 'Username',
            'auth.password': 'Password',
            'auth.nickname': 'Nickname',
            'auth.login': 'Login',
            'auth.register': 'Register',
            'auth.no_account': 'No account?',
            'auth.have_account': 'Already have an account?',
            'auth.login.required': 'Enter username and password.',
            'auth.login.success': 'Login successful!',
            'auth.login.failed': 'Login failed',
            'auth.register.success': 'Registration completed. Please sign in.',
            'auth.register.failed': 'Registration failed',
            'auth.server_error': 'Server connection error',
            'auth.session_required': 'Session check failed, login required',
            'main.conversations': '🔒 Conversations',
            'main.search_placeholder': 'Search conversations...',
            'main.select_room': 'Select a conversation',
            'main.select_room_desc': 'Choose a conversation from the left\\nor start a new chat',
            'main.new_chat': '➕ Start New Chat',
            'main.status.online': 'Online',
            'main.shortcut.new_chat': 'to start quickly',
            'main.room.pin': 'Pin to Top',
            'main.room.unpin': 'Unpin',
            'main.room.mute': 'Mute',
            'main.room.unmute': 'Unmute',
            'main.connection.connecting': 'Connecting...',
            'socket.connected': 'Connected',
            'socket.disconnected': 'Disconnected',
            'socket.reconnecting': 'Reconnecting... ({attempt})',
            'settings.title': '🎨 Display Settings',
            'settings.language': 'Language',
            'settings.default': 'Default',
            'common.close': 'Close',
            'common.save': 'Save',
            'common.cancel': 'Cancel',
            'common.search': 'Search',
            'language.auto': 'Auto',
            'language.ko': '한국어',
            'language.en': 'English',
            'errors.generic': 'An error occurred while processing the request.',
            'errors.network': 'Server connection error',
            'profile.edit': '⚙ Edit Profile',
            'profile.image.alt': 'Profile',
            'feature.poll.create': 'Poll created.',
            'feature.poll.create_failed': 'Failed to create poll.',
            'feature.poll.close_confirm': 'Close this poll?',
            'feature.file.delete_confirm': 'Delete this file?',
            'feature.file.deleted': 'File deleted.',
            'feature.file.delete_failed': 'Failed to delete file.',
            'feature.pinned': 'Pinned as announcement.',
            'feature.unpinned': 'Announcement removed.',
            'feature.admin.updated': 'Admin settings updated.',
            'feature.search.no_result': 'No results found',
            'notify.new_message': 'New message',
            'notify.mention_title': 'Mentioned - {sender}',
            'notify.unsupported': 'This browser does not support notifications.',
            'message.unread_divider': 'Unread messages below',
            'message.all_read': 'Read by everyone',
            'message.unread_count': '{count} unread',
            'message.decrypting': '[decrypting...]',
            'message.encrypted': '[encrypted message]',
            'message.reply': 'Reply',
            'message.reaction': 'Reaction',
            'message.edit': 'Edit',
            'message.delete': 'Delete',
            'message.file_invalid_path': '[invalid image path]',
            'message.sender.unknown': 'User',
            'message.reply_from': '↩ {sender}\'s message'
        }
    };

    var EXTRA_KO = {
        'main.status.offline': '오프라인',
        'settings.theme_mode': '테마 모드',
        'settings.theme_color': '테마 색상',
        'settings.chat_background': '채팅 배경',
        'settings.theme.dark': '🌙 다크',
        'settings.theme.light': '☀️ 라이트',
        'settings.theme.system': '💻 시스템',
        'settings.reset_done': '설정이 초기화되었습니다',
        'rooms.default_name': '대화방',
        'rooms.group': '그룹',
        'rooms.empty': '대화방이 없습니다,<br>새 대화를 시작해보세요!',
        'rooms.preview.new_chat': '새 대화',
        'rooms.preview.image': '📷 이미지',
        'rooms.preview.file': '📎 파일',
        'rooms.preview.system': '🔔 시스템메시지',
        'rooms.preview.encrypted': '🔒 암호화된 메시지',
        'rooms.preview.message': '메시지',
        'rooms.member_count': '{count}명 참여 중',
        'rooms.members_total': '👥 총 {count}명 참여 중',
        'rooms.status.online_detail': '🟢 온라인',
        'rooms.status.offline_detail': '⚪ 오프라인',
        'rooms.context.open': '💬 열기',
        'rooms.context.pin': '📌 상단 고정',
        'rooms.context.unpin': '📌 고정 해제',
        'rooms.context.mute': '🔕 알림 끄기',
        'rooms.context.unmute': '🔔 알림 켜기',
        'rooms.context.leave': '🚪 나가기',
        'rooms.reordered': '대화방 순서가 변경되었습니다.',
        'rooms.select_first': '먼저 대화방을 선택해주세요.',
        'rooms.rename_prompt': '새 대화방 이름:',
        'rooms.me_badge': '(나)',
        'rooms.load_failed': '대화방 목록 로드 실패: {error}',
        'rooms.messages_load_failed': '메시지 로드 실패: {error}',
        'rooms.users_load_failed': '사용자 목록을 불러오지 못했습니다.',
        'rooms.create_failed': '대화방 생성 실패: {error}',
        'rooms.invite_select_user': '초대할 사용자를 선택해주세요.',
        'rooms.invite_success': '멤버를 초대했습니다.',
        'rooms.invite_failed': '초대에 실패했습니다: {error}',
        'rooms.members_load_failed': '멤버 정보를 불러오는데 실패했습니다.',
        'rooms.leave_confirm': '"{room}" 대화방을 나가시겠습니까?\n\n⚠️ 나가면 대화 내역을 더 이상 볼 수 없습니다.',
        'rooms.leave_success': '대화방을 나갔습니다.',
        'rooms.leave_failed': '대화방 나가기에 실패했습니다.',
        'rooms.online_none': '온라인 사용자가 없습니다',
        'rooms.start_chat_failed': '대화 시작 실패: {error}',
        'rooms.start_chat_error': '대화 시작 오류: {error}',
        'poll.option': '옵션',
        'poll.option_limit': '옵션은 최대 10개까지 가능합니다.',
        'poll.question_required': '질문을 입력해주세요.',
        'poll.options_required': '최소 2개의 옵션이 필요합니다.',
        'poll.options_duplicated': '중복된 옵션이 있습니다.',
        'poll.closed': '투표가 종료되었습니다.',
        'poll.close': '투표 종료',
        'poll.close_failed': '투표 종료에 실패했습니다.',
        'poll.vote_failed': '투표에 실패했습니다.',
        'poll.load_failed': '투표 목록을 불러올 수 없습니다.',
        'poll.status.closed': '종료됨',
        'poll.status.active': '진행중',
        'poll.deadline_days': '{count}일 후 마감',
        'poll.deadline_hours': '{count}시간 후 마감',
        'poll.deadline_minutes': '{count}분 후 마감',
        'poll.deadline_expired': '마감됨',
        'poll.total_votes': '총 {count}표',
        'files.none': '파일이 없습니다',
        'files.download': '다운로드',
        'files.delete': '삭제',
        'pin.default': '공지사항',
        'pin.set': '공지로 설정',
        'pin.create_failed': '공지 고정에 실패했습니다.',
        'pin.delete_confirm': '이 공지를 삭제하시겠습니까?',
        'pin.delete_failed': '공지 삭제에 실패했습니다.',
        'admin.badge': '👑 관리자',
        'admin.grant_short': '지정',
        'admin.revoke_short': '해제',
        'admin.granted': '관리자로 지정되었습니다.',
        'admin.revoked': '관리자 권한이 해제되었습니다.',
        'admin.update_failed': '관리자 설정에 실패했습니다.',
        'search.in_chat_placeholder': '대화 내 검색...',
        'search.no_result_short': '결과 없음',
        'search.query_or_filter_required': '검색어를 입력하거나 필터를 선택해주세요.',
        'search.query_min_2': '검색어는 2자 이상 입력해주세요.',
        'search.failed': '검색에 실패했습니다.',
        'search.results_aria': '검색 결과',
        'search.load_more': '검색 결과 더 보기',
        'common.load_more': '더 보기',
        'network.offline': '⚠️ 오프라인 상태입니다',
        'network.retry': '다시 시도',
        'network.restored': '인터넷 연결이 복구되었습니다.',
        'network.still_offline': '아직 오프라인 상태입니다.',
        'message.loading_previous': '이전 메시지 불러오는 중...',
        'message.render_error': '메시지 렌더링 오류',
        'message.deleted_placeholder': '[삭제된 메시지]',
        'message.edited': '(수정됨)',
        'message.edit_prompt': '메시지 수정:',
        'message.delete_confirm': '이 메시지를 삭제하시겠습니까?',
        'reaction.add': '리액션 추가',
        'reaction.failed': '리액션 처리에 실패했습니다.',
        'reaction.picker': '리액션 선택',
        'reaction.with_emoji': '리액션 {emoji}',
        'socket.disconnected': '서버 연결이 끊어졌습니다.',
        'socket.disconnected_retry': '서버 연결이 끊어졌습니다. 잠시 후 다시 시도해주세요.',
        'upload.progress_25': '📤 파일 업로드 시작... 25%',
        'upload.progress_50': '📤 파일 업로드 중... 50%',
        'upload.progress_75': '📤 거의 완료... 75%',
        'upload.done': '파일 업로드 완료!',
        'upload.sent': '파일이 전송되었습니다.',
        'upload.failed': '파일 업로드에 실패했습니다.',
        'upload.response_parse_failed': '파일 업로드 응답 처리 실패',
        'upload.socket_disconnected_after_upload': '서버 연결이 끊어졌습니다. 파일은 업로드되었으나 메시지 전송에 실패했습니다.',
        'upload.token_missing': '업로드 토큰 발급에 실패했습니다. 다시 업로드해주세요.',
        'upload.timeout': '파일 업로드 시간이 초과되었습니다.',
        'upload.timeout_detail': '파일 업로드 시간이 초과되었습니다. 더 작은 파일을 시도하거나 네트워크 연결을 확인하세요.',
        'upload.size_limit_16mb': '파일 크기는 16MB 이하여야 합니다.',
        'profile.saved': '프로필이 저장되었습니다.',
        'profile.save_failed': '프로필 저장에 실패했습니다.',
        'profile.nickname_min': '닉네임은 2자 이상이어야 합니다.',
        'profile.image_type_invalid': 'JPG, PNG, GIF, WEBP 이미지만 업로드 가능합니다.',
        'profile.image_size_limit': '이미지 크기는 5MB 이하여야 합니다.',
        'profile.image_uploaded': '프로필 사진이 업로드되었습니다.',
        'profile.image_upload_failed': '이미지 업로드에 실패했습니다.',
        'profile.image_not_found': '삭제할 프로필 사진이 없습니다.',
        'profile.image_delete_confirm': '프로필 사진을 삭제하시겠습니까?',
        'profile.image_deleted': '프로필 사진이 삭제되었습니다.',
        'profile.image_delete_failed': '삭제에 실패했습니다.',
        'profile.password_all_required': '모든 필드를 입력해주세요.',
        'profile.password_mismatch': '새 비밀번호가 일치하지 않습니다.',
        'profile.password_too_short': '비밀번호는 8자 이상이어야 합니다.',
        'profile.password_complexity': '비밀번호는 영문자와 숫자를 포함해야 합니다.',
        'profile.password_changed': '비밀번호가 변경되었습니다.',
        'profile.password_change_failed': '비밀번호 변경에 실패했습니다.',
        'profile.delete_account_confirm': '정말 탈퇴하시겠습니까?\n\n⚠️ 이 작업은 되돌릴 수 없습니다.',
        'profile.delete_account_prompt': '탈퇴를 진행하려면 현재 비밀번호를 입력해주세요:',
        'profile.password_required': '비밀번호를 입력해야 합니다.',
        'profile.delete_account_done': '회원 탈퇴가 완료되었습니다.',
        'profile.delete_account_failed': '회원 탈퇴에 실패했습니다.',
        'auth.password_too_short': '비밀번호는 최소 8자 이상이어야 합니다.',
        'auth.password_complexity': '비밀번호는 영문과 숫자를 포함해야 합니다.',
        'common.unknown': '알 수 없음',
        'mention.toast': '{sender}님이 멘션했습니다.',
        'preview.image': '📷 이미지',
        'preview.file': '📎 파일',
        'preview.system': '🔔 시스템메시지',
        'preview.message': '메시지',
        'time.just_now': '방금 전',
        'time.minutes_ago': '{minutes}분 전',
        'time.today': '오늘',
        'time.yesterday': '어제',
        'toast.success': '완료',
        'toast.info': '안내',
        'toast.warning': '경고',
        'toast.error': '오류',
        'typing.single': '{user}님이 입력 중...',
        'typing.double': '{user1}, {user2}님이 입력 중...',
        'typing.multi': '{user1}님 외 {count}명이 입력 중...'
    };

    var EXTRA_EN = {
        'main.status.offline': 'Offline',
        'settings.theme_mode': 'Theme Mode',
        'settings.theme_color': 'Theme Color',
        'settings.chat_background': 'Chat Background',
        'settings.theme.dark': '🌙 Dark',
        'settings.theme.light': '☀️ Light',
        'settings.theme.system': '💻 System',
        'settings.reset_done': 'Settings were reset.',
        'rooms.default_name': 'Room',
        'rooms.group': 'Group',
        'rooms.empty': 'No rooms yet.<br>Start a new conversation!',
        'rooms.preview.new_chat': 'New conversation',
        'rooms.preview.image': '📷 Image',
        'rooms.preview.file': '📎 File',
        'rooms.preview.system': '🔔 System message',
        'rooms.preview.encrypted': '🔒 Encrypted message',
        'rooms.preview.message': 'Message',
        'rooms.member_count': '{count} members',
        'rooms.members_total': '👥 {count} members',
        'rooms.status.online_detail': '🟢 Online',
        'rooms.status.offline_detail': '⚪ Offline',
        'rooms.context.open': '💬 Open',
        'rooms.context.pin': '📌 Pin to top',
        'rooms.context.unpin': '📌 Unpin',
        'rooms.context.mute': '🔕 Mute',
        'rooms.context.unmute': '🔔 Unmute',
        'rooms.context.leave': '🚪 Leave',
        'rooms.reordered': 'Room order updated.',
        'rooms.select_first': 'Select a room first.',
        'rooms.rename_prompt': 'New room name:',
        'rooms.me_badge': '(me)',
        'rooms.load_failed': 'Failed to load room list: {error}',
        'rooms.messages_load_failed': 'Failed to load messages: {error}',
        'rooms.users_load_failed': 'Failed to load user list.',
        'rooms.create_failed': 'Failed to create room: {error}',
        'rooms.invite_select_user': 'Select users to invite.',
        'rooms.invite_success': 'Members invited.',
        'rooms.invite_failed': 'Invite failed: {error}',
        'rooms.members_load_failed': 'Failed to load members.',
        'rooms.leave_confirm': 'Leave "{room}"?\n\n⚠️ You will no longer see this room history.',
        'rooms.leave_success': 'You left the room.',
        'rooms.leave_failed': 'Failed to leave room.',
        'rooms.online_none': 'No online users',
        'rooms.start_chat_failed': 'Failed to start chat: {error}',
        'rooms.start_chat_error': 'Error while starting chat: {error}',
        'poll.option': 'Option',
        'poll.option_limit': 'Up to 10 options are allowed.',
        'poll.question_required': 'Enter a question.',
        'poll.options_required': 'At least two options are required.',
        'poll.options_duplicated': 'Duplicate options are not allowed.',
        'poll.closed': 'Poll closed.',
        'poll.close': 'Close Poll',
        'poll.close_failed': 'Failed to close poll.',
        'poll.vote_failed': 'Failed to submit vote.',
        'poll.load_failed': 'Failed to load polls.',
        'poll.status.closed': 'Closed',
        'poll.status.active': 'Open',
        'poll.deadline_days': 'Ends in {count} day(s)',
        'poll.deadline_hours': 'Ends in {count} hour(s)',
        'poll.deadline_minutes': 'Ends in {count} minute(s)',
        'poll.deadline_expired': 'Expired',
        'poll.total_votes': '{count} vote(s)',
        'files.none': 'No files',
        'files.download': 'Download',
        'files.delete': 'Delete',
        'pin.default': 'Announcement',
        'pin.set': 'Set as announcement',
        'pin.create_failed': 'Failed to pin announcement.',
        'pin.delete_confirm': 'Delete this announcement?',
        'pin.delete_failed': 'Failed to delete announcement.',
        'admin.badge': '👑 Admin',
        'admin.grant_short': 'Grant',
        'admin.revoke_short': 'Revoke',
        'admin.granted': 'Granted admin role.',
        'admin.revoked': 'Revoked admin role.',
        'admin.update_failed': 'Failed to update admin settings.',
        'search.in_chat_placeholder': 'Search in chat...',
        'search.no_result_short': 'No result',
        'search.query_or_filter_required': 'Enter a query or choose filters.',
        'search.query_min_2': 'Enter at least 2 characters.',
        'search.failed': 'Search failed.',
        'search.results_aria': 'Search results',
        'search.load_more': 'Load more search results',
        'common.load_more': 'Load more',
        'network.offline': '⚠️ You are offline',
        'network.retry': 'Retry',
        'network.restored': 'Internet connection restored.',
        'network.still_offline': 'Still offline.',
        'message.loading_previous': 'Loading previous messages...',
        'message.render_error': 'Message render error',
        'message.deleted_placeholder': '[deleted message]',
        'message.edited': '(edited)',
        'message.edit_prompt': 'Edit message:',
        'message.delete_confirm': 'Delete this message?',
        'reaction.add': 'Add reaction',
        'reaction.failed': 'Failed to update reaction.',
        'reaction.picker': 'Select reaction',
        'reaction.with_emoji': 'Reaction {emoji}',
        'socket.disconnected': 'Server connection lost.',
        'socket.disconnected_retry': 'Server connection lost. Please try again shortly.',
        'upload.progress_25': '📤 Upload started... 25%',
        'upload.progress_50': '📤 Uploading... 50%',
        'upload.progress_75': '📤 Almost done... 75%',
        'upload.done': 'Upload complete!',
        'upload.sent': 'File sent.',
        'upload.failed': 'File upload failed.',
        'upload.response_parse_failed': 'Failed to process upload response.',
        'upload.socket_disconnected_after_upload': 'Server disconnected. File uploaded, but message send failed.',
        'upload.token_missing': 'Upload token missing. Please upload again.',
        'upload.timeout': 'File upload timed out.',
        'upload.timeout_detail': 'File upload timed out. Try a smaller file or check network connectivity.',
        'upload.size_limit_16mb': 'File size must be 16MB or less.',
        'profile.saved': 'Profile saved.',
        'profile.save_failed': 'Failed to save profile.',
        'profile.nickname_min': 'Nickname must be at least 2 characters.',
        'profile.image_type_invalid': 'Only JPG, PNG, GIF, WEBP images are allowed.',
        'profile.image_size_limit': 'Image size must be 5MB or less.',
        'profile.image_uploaded': 'Profile image uploaded.',
        'profile.image_upload_failed': 'Failed to upload profile image.',
        'profile.image_not_found': 'No profile image to delete.',
        'profile.image_delete_confirm': 'Delete profile image?',
        'profile.image_deleted': 'Profile image deleted.',
        'profile.image_delete_failed': 'Failed to delete profile image.',
        'profile.password_all_required': 'Fill in all fields.',
        'profile.password_mismatch': 'New passwords do not match.',
        'profile.password_too_short': 'Password must be at least 8 characters.',
        'profile.password_complexity': 'Password must include letters and numbers.',
        'profile.password_changed': 'Password changed.',
        'profile.password_change_failed': 'Failed to change password.',
        'profile.delete_account_confirm': 'Are you sure you want to delete your account?\n\n⚠️ This action cannot be undone.',
        'profile.delete_account_prompt': 'Enter current password to continue:',
        'profile.password_required': 'Password is required.',
        'profile.delete_account_done': 'Account deleted.',
        'profile.delete_account_failed': 'Failed to delete account.',
        'auth.password_too_short': 'Password must be at least 8 characters long.',
        'auth.password_complexity': 'Password must include both letters and numbers.',
        'common.unknown': 'Unknown',
        'mention.toast': '{sender} mentioned you.',
        'preview.image': '📷 Image',
        'preview.file': '📎 File',
        'preview.system': '🔔 System message',
        'preview.message': 'Message',
        'time.just_now': 'Just now',
        'time.minutes_ago': '{minutes} minute(s) ago',
        'time.today': 'Today',
        'time.yesterday': 'Yesterday',
        'toast.success': 'Success',
        'toast.info': 'Info',
        'toast.warning': 'Warning',
        'toast.error': 'Error',
        'typing.single': '{user} is typing...',
        'typing.double': '{user1}, {user2} are typing...',
        'typing.multi': '{user1} and {count} other(s) are typing...'
    };

    BUILTIN.ko = Object.assign({}, BUILTIN.ko, EXTRA_KO);
    BUILTIN.en = Object.assign({}, BUILTIN.en, EXTRA_EN);

    var LITERAL_KEY_MAP = {
        '연결됨': 'socket.connected',
        '연결 끊김': 'socket.disconnected',
        '새 메시지': 'notify.new_message',
        '여기서부터 읽지 않음': 'message.unread_divider',
        '모두 읽음': 'message.all_read',
        '재연결 중...': 'socket.reconnecting',
        '로그인 성공!': 'auth.login.success',
        '아이디와 비밀번호를 입력하세요.': 'auth.login.required',
        '회원가입 완료! 로그인해주세요.': 'auth.register.success',
        '대화방을 나갔습니다.': 'rooms.leave_success',
        '파일 업로드 실패': 'upload.failed',
        '파일 업로드 완료!': 'upload.done',
        '프로필이 저장되었습니다.': 'profile.saved',
        '프로필 사진이 삭제되었습니다.': 'profile.image_deleted',
        '투표가 생성되었습니다.': 'feature.poll.create',
        '투표 생성에 실패했습니다.': 'feature.poll.create_failed'
    };

    function normalizeLocale(value) {
        var raw = String(value || '').trim().toLowerCase();
        if (!raw) return DEFAULT_LOCALE;
        if (raw.indexOf('en') === 0) return 'en';
        if (raw.indexOf('ko') === 0) return 'ko';
        return DEFAULT_LOCALE;
    }

    function toDisplayLocale(code) {
        return normalizeLocale(code) === 'en' ? 'en-US' : 'ko-KR';
    }

    function parsePreference(value) {
        var normalized = String(value || 'auto').trim().toLowerCase();
        if (normalized === 'ko' || normalized === 'en' || normalized === 'auto') {
            return normalized;
        }
        return 'auto';
    }

    function detectSystemLocale() {
        try {
            var navLang = (navigator.languages && navigator.languages.length > 0)
                ? navigator.languages[0]
                : navigator.language;
            return normalizeLocale(navLang);
        } catch (e) {
            return DEFAULT_LOCALE;
        }
    }

    function interpolate(template, vars) {
        if (!vars) return template;
        return String(template).replace(/\{(\w+)\}/g, function (_m, key) {
            if (Object.prototype.hasOwnProperty.call(vars, key)) {
                return String(vars[key]);
            }
            return '{' + key + '}';
        });
    }

    function t(key, fallback, vars) {
        var text = catalog[key];
        if (typeof text !== 'string') {
            text = (BUILTIN[locale] && BUILTIN[locale][key])
                || (BUILTIN[DEFAULT_LOCALE] && BUILTIN[DEFAULT_LOCALE][key])
                || fallback
                || key;
        }
        return interpolate(text, vars);
    }

    function localizeText(text) {
        if (locale !== 'en') return text;
        var key = LITERAL_KEY_MAP[String(text || '')];
        if (!key) return text;
        return t(key, text);
    }

    function getPreference() {
        try {
            return parsePreference(localStorage.getItem(STORAGE_KEY));
        } catch (e) {
            return 'auto';
        }
    }

    function savePreference(value) {
        try {
            localStorage.setItem(STORAGE_KEY, parsePreference(value));
        } catch (e) {
            // ignore
        }
    }

    function resolveLocaleFromPreference(pref) {
        if (pref === 'ko' || pref === 'en') return pref;
        return detectSystemLocale();
    }

    async function fetchCatalog(localeCode) {
        var endpoint = '/api/i18n/web?lang=' + encodeURIComponent(localeCode);
        try {
            var response = await fetch(endpoint, { method: 'GET' });
            if (!response.ok) return {};
            var payload = await response.json();
            if (payload && typeof payload === 'object' && payload.catalog && typeof payload.catalog === 'object') {
                return payload.catalog;
            }
        } catch (e) {
            // ignore network errors
        }
        return {};
    }

    function setText(selector, key, fallback) {
        var el = document.querySelector(selector);
        if (!el) return;
        el.textContent = t(key, fallback);
    }

    function setPlaceholder(selector, key, fallback) {
        var el = document.querySelector(selector);
        if (!el) return;
        el.setAttribute('placeholder', t(key, fallback));
    }

    function applyDataI18n() {
        document.querySelectorAll('[data-i18n]').forEach(function (el) {
            var key = el.getAttribute('data-i18n') || '';
            if (!key) return;
            var fallback = el.getAttribute('data-i18n-fallback') || el.textContent || '';
            el.textContent = t(key, fallback);
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
            var key = el.getAttribute('data-i18n-placeholder') || '';
            if (!key) return;
            var fallback = el.getAttribute('placeholder') || '';
            el.setAttribute('placeholder', t(key, fallback));
        });
        document.querySelectorAll('[data-i18n-title]').forEach(function (el) {
            var key = el.getAttribute('data-i18n-title') || '';
            if (!key) return;
            var fallback = el.getAttribute('title') || '';
            el.setAttribute('title', t(key, fallback));
        });
    }

    function applyAuthSwitchText() {
        var regWrap = document.getElementById('switchToRegisterWrap');
        var regLink = document.getElementById('showRegister');
        if (regWrap && regLink) {
            if (regWrap.firstChild && regWrap.firstChild.nodeType === 3) {
                regWrap.firstChild.nodeValue = t('auth.no_account', 'No account?') + ' ';
            }
            regLink.textContent = t('auth.register', 'Register');
        }

        var loginWrap = document.getElementById('switchToLoginWrap');
        var loginLink = document.getElementById('showLogin');
        if (loginWrap && loginLink) {
            if (loginWrap.firstChild && loginWrap.firstChild.nodeType === 3) {
                loginWrap.firstChild.nodeValue = t('auth.have_account', 'Already have an account?') + ' ';
            }
            loginLink.textContent = t('auth.login', 'Login');
        }
    }

    function applyStaticTexts() {
        document.documentElement.lang = locale;
        document.title = t('app.page_title', '🔒 Intranet Messenger (E2E Encrypted)');

        setText('.skip-link', 'a11y.skip_main', '메인 콘텐츠로 건너뛰기');
        setText('#authContainer h1', 'app.title', '🔒 사내 메신저');
        setText('#authContainer .subtitle', 'app.subtitle', '종단간 암호화로 안전하게 소통하세요');
        setText('.encryption-badge', 'app.encryption_badge', '🔒 E2E 암호화 적용');
        setText('#loginBtn', 'auth.login', '로그인');
        setText('#registerBtn', 'auth.register', '회원가입');
        setText('#appContainer .sidebar-header h2', 'main.conversations', '🔒 대화');
        setPlaceholder('#searchInput', 'main.search_placeholder', '대화 검색...');
        setText('#settingsModalTitle', 'settings.title', '🎨 화면 설정');
        setText('#languageSectionLabel', 'settings.language', '언어');
        setText('#resetSettingsBtn', 'settings.default', '기본값');
        setText('#closeSettingsBtn', 'common.close', '닫기');
        setText('#closeHelpBtn', 'common.close', '닫기');

        var settingsSections = document.querySelectorAll('#settingsModal .settings-section-title');
        if (settingsSections[0]) settingsSections[0].textContent = t('settings.theme_mode', '테마 모드');
        if (settingsSections[1]) settingsSections[1].textContent = t('settings.theme_color', '테마 색상');
        if (settingsSections[2]) settingsSections[2].textContent = t('settings.chat_background', '채팅 배경');

        var darkBtn = document.querySelector('#settingsModal .theme-toggle-btn[data-theme="dark"]');
        var lightBtn = document.querySelector('#settingsModal .theme-toggle-btn[data-theme="light"]');
        var systemBtn = document.querySelector('#settingsModal .theme-toggle-btn[data-theme="system"]');
        if (darkBtn) darkBtn.textContent = t('settings.theme.dark', '🌙 다크');
        if (lightBtn) lightBtn.textContent = t('settings.theme.light', '☀️ 라이트');
        if (systemBtn) systemBtn.textContent = t('settings.theme.system', '💻 시스템');

        var loginForm = document.getElementById('loginForm');
        if (loginForm) {
            var labels = loginForm.querySelectorAll('label');
            if (labels[0]) labels[0].textContent = t('auth.username', '아이디');
            if (labels[1]) labels[1].textContent = t('auth.password', '비밀번호');
        }
        setPlaceholder('#loginUsername', 'auth.username', '아이디');
        setPlaceholder('#loginPassword', 'auth.password', '비밀번호');

        var registerForm = document.getElementById('registerForm');
        if (registerForm) {
            var registerLabels = registerForm.querySelectorAll('.form-group > label');
            if (registerLabels[0]) registerLabels[0].textContent = t('auth.username', '아이디');
            if (registerLabels[1]) registerLabels[1].textContent = t('auth.password', '비밀번호');
            if (registerLabels[2]) registerLabels[2].textContent = t('auth.nickname', '닉네임');
        }

        applyAuthSwitchText();
        updateLanguageSelectorOptions();
    }

    function updateLanguageSelectorOptions() {
        var select = document.getElementById('languageSelect');
        if (!select) return;

        Array.from(select.options).forEach(function (option) {
            if (option.value === 'auto') option.textContent = t('language.auto', 'Auto');
            if (option.value === 'ko') option.textContent = t('language.ko', '한국어');
            if (option.value === 'en') option.textContent = t('language.en', 'English');
        });
        select.value = preference;
    }

    function applyAll() {
        applyDataI18n();
        applyStaticTexts();
    }

    function emitLanguageChanged() {
        window.dispatchEvent(
            new CustomEvent('app-language-changed', {
                detail: {
                    locale: locale,
                    displayLocale: toDisplayLocale(locale),
                    preference: preference
                }
            })
        );
    }

    async function setLanguage(nextPreference, options) {
        options = options || {};
        var silent = !!options.silent;
        var persist = options.persist !== false;

        preference = parsePreference(nextPreference);
        locale = resolveLocaleFromPreference(preference);
        if (persist) savePreference(preference);

        var remoteCatalog = await fetchCatalog(locale);
        catalog = Object.assign({}, BUILTIN[DEFAULT_LOCALE], BUILTIN[locale], remoteCatalog);

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', applyAll, { once: true });
        } else {
            applyAll();
        }

        if (!silent) emitLanguageChanged();
    }

    function wireLanguageSelector() {
        var select = document.getElementById('languageSelect');
        if (!select || select._i18nBound) return;
        select._i18nBound = true;
        select.addEventListener('change', function () {
            setLanguage(select.value);
        });
    }

    async function initWebI18n() {
        preference = getPreference();
        await setLanguage(preference, { silent: true, persist: false });
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', wireLanguageSelector, { once: true });
        } else {
            wireLanguageSelector();
        }
        emitLanguageChanged();
    }

    window.t = t;
    window.localizeText = localizeText;
    window.getAppLanguage = function () { return locale; };
    window.getAppDisplayLocale = function () { return toDisplayLocale(locale); };
    window.getAppLanguagePreference = function () { return preference; };
    window.setAppLanguage = setLanguage;
    window.applyI18n = applyAll;
    window.initWebI18n = initWebI18n;
    window.i18nReady = initWebI18n();
})();
