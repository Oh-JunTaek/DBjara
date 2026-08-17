"""
DBjara - 다국어 지원 (i18n / Internationalization) 모듈
한국어(ko), 영어(en) 및 향후 다국어 확장을 지원하는 번역 관리 엔진입니다.
"""

from typing import Dict, Any

# 다국어 번역 딕셔너리
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ko": {
        # 앱 일반
        "app_title": "DBjara - LoL 솔로 랭크 통제기",
        "app_name": "DBjara (디비자라)",
        "app_sub": "친구와의 게임은 즐겁게, 혼자만의 밤샘 솔랭은 강력하게 통제합니다.",
        "save_success_title": "저장 완료",
        "save_success_msg": "설정이 성공적으로 저장 및 적용되었습니다.",
        "copied_title": "복사 완료",
        "copied_msg": "비밀키가 클립보드에 복사되었습니다.",
        
        # 시스템 트레이
        "tray_status_prefix": "통제 모드: ",
        "tray_mode_high": "상 (전체 차단)",
        "tray_mode_medium": "중 (솔로 금지)",
        "tray_mode_low": "하 (시간 제한)",
        "tray_open_settings": "설정 열기 (DBjara)",
        "tray_check_update": "업데이트 확인",
        "tray_exit": "DBjara 종료",
        
        # 알림 메시지
        "notif_night_title": "DBjara - 야간 강제 차단",
        "notif_night_msg": "야간 시간대입니다. 게임이 즉시 종료되었습니다. 어서 주무세요.",
        "notif_high_title": "DBjara - 실행 차단",
        "notif_high_msg": "통제 강도 [상] 설정으로 인해 롤 실행이 차단되었습니다.",
        "notif_solo_title": "DBjara - 솔로 매칭 취소",
        "notif_solo_msg": "1인 솔로 랭크 매칭이 감지되어 취소되었습니다.\n(2인 이상 다인큐만 가능합니다)",
        "notif_time_title": "DBjara - 일일 시간 초과",
        "notif_time_msg": "오늘의 솔로 허용 시간({minutes}분)을 모두 소진하여 종료되었습니다.",
        "notif_time_block_msg": "오늘의 일일 솔로 허용 시간을 초과하여 매칭이 차단되었습니다.",
        "notif_update_title": "DBjara 새 버전 업데이트 알림",
        "notif_update_msg": "새로운 버전 ({tag})이 출시되었습니다.\n트레이 메뉴의 설정을 열어 확인하세요.",

        # 설정 화면 - 언어 선택
        "sec_language": " 언어 설정 (Language) ",
        "lang_label": "표시 언어:",

        # 설정 화면 - 섹션 1: 통제 강도
        "sec_mode": " 통제 강도 설정 ",
        "mode_high": "상 (High): 롤 실행 자체 차단",
        "mode_medium": "중 (Medium): 솔로(1인) 플레이 금지 (권장)",
        "mode_low": "하 (Low): 일일 솔로 시간 제한",
        "daily_limit_label": "하루 최대 솔로 시간: {minutes}분",

        # 설정 화면 - 섹션 2: 야간 시간 통제
        "sec_night": " 야간 시간 강제 차단 (디비자라 모드) ",
        "night_lock_chk": "야간 시간대 게임 완전 차단 (동반자 무관 강제 종료)",
        "night_start": "차단 시작:",
        "night_end": "~ 종료:",

        # 설정 화면 - 섹션 3: 동반자 OTP & 부팅
        "sec_lock": " 자제력 자물쇠 (동반자 OTP & 자동 실행) ",
        "otp_chk": "동반자 OTP 자물쇠 활성화 (설정 변경/앱 종료 시 OTP 요구)",
        "otp_view_btn": "동반자 등록 QR / 비밀키 보기",
        "auto_start_chk": "윈도우 부팅 시 자동 실행 (백그라운드 상시 감시)",

        # 설정 화면 - 섹션 4: Riot ID 전적 검증
        "sec_riot": " Riot ID 전적 검증 (PC방 몰래 솔랭 방지) ",
        "riot_desc": "소환사 Riot ID를 등록하면 PC방 등 외부에서 몰래 솔랭한 기록도 감지합니다.",
        "riot_id_label": "Riot ID (이름#태그):",

        # 설정 화면 - 섹션 5: 통계 및 업데이트
        "sec_meta": " 통계 및 업데이트 설정 ",
        "telemetry_chk": "익명 사용 통계 전송 동의 (차단 횟수 등 비식별 데이터)",
        "auto_update_chk": "프로그램 시작 시 최신 버전 자동 확인",
        "btn_save": "설정 저장 및 적용",
        "btn_update_check": "업데이트 확인",

        # OTP 인증 팝업
        "otp_auth_title": "동반자 OTP 인증 필요",
        "otp_auth_desc": "설정 변경 또는 앱 종료를 위해\n동반자(친구)의 스마트폰 OTP 번호 6자리를 입력하세요.",
        "otp_auth_btn": "인증하기",
        "otp_cancel_btn": "취소",
        "otp_err_mismatch": "번호가 일치하지 않습니다. 다시 확인하세요.",

        # OTP 등록 팝업
        "otp_setup_title": "동반자 등록 (Google Authenticator) - DBjara",
        "otp_setup_head": "동반자(친구/가족) 스마트폰 등록",
        "otp_setup_sub": "친구의 스마트폰(Google Authenticator 앱 등)으로\n아래 QR 코드를 스캔하거나 비밀키를 직접 입력해 등록하세요.",
        "otp_key_title": "등록용 비밀키(Secret Key):",
        "otp_copy_btn": "복사",
        "otp_test_label": "등록 후 친구의 폰에 생성된 6자리 번호로 테스트:",
        "otp_test_btn": "테스트 및 등록 완료",
        "otp_test_empty": "6자리 번호를 입력해주세요.",
        "otp_test_success": "동반자 OTP가 정상적으로 등록 및 검증되었습니다.",
        
        # 업데이트 확인 팝업
        "update_found_title": "새 버전 발견",
        "update_found_msg": "새로운 버전 ({tag})이 출시되었습니다.\n\n다운로드 페이지를 여시겠습니까?",
        "update_latest_title": "최신 버전",
        "update_latest_msg": "현재 최신 버전({version})을 사용 중입니다.",
    },
    "en": {
        # App General
        "app_title": "DBjara - LoL Solo Rank Blocker",
        "app_name": "DBjara",
        "app_sub": "Enjoy duo games with friends, strictly block solo queue bingeing.",
        "save_success_title": "Saved",
        "save_success_msg": "Settings have been successfully saved and applied.",
        "copied_title": "Copied",
        "copied_msg": "Secret key copied to clipboard.",
        
        # System Tray
        "tray_status_prefix": "Mode: ",
        "tray_mode_high": "High (Block All)",
        "tray_mode_medium": "Medium (Block Solo)",
        "tray_mode_low": "Low (Time Limit)",
        "tray_open_settings": "Open Settings (DBjara)",
        "tray_check_update": "Check for Updates",
        "tray_exit": "Exit DBjara",
        
        # Notifications
        "notif_night_title": "DBjara - Night Forced Sleep",
        "notif_night_msg": "It's night time! Game was closed immediately. Go to sleep!",
        "notif_high_title": "DBjara - Launch Blocked",
        "notif_high_msg": "League client launch blocked due to [High] mode setting.",
        "notif_solo_title": "DBjara - Solo Match Canceled",
        "notif_solo_msg": "Solo matchmaking detected and canceled!\n(Only party queue with friends is allowed)",
        "notif_time_title": "DBjara - Daily Limit Reached",
        "notif_time_msg": "Daily solo time limit ({minutes} min) exceeded. League client closed.",
        "notif_time_block_msg": "Daily solo time limit exceeded. Matchmaking blocked.",
        "notif_update_title": "DBjara Update Available",
        "notif_update_msg": "New version ({tag}) is available!\nOpen settings from tray to download.",

        # Settings - Language
        "sec_language": " Language Settings ",
        "lang_label": "Display Language:",

        # Settings - Section 1: Mode
        "sec_mode": " Enforcement Intensity ",
        "mode_high": "High: Block League entirely",
        "mode_medium": "Medium: Block Solo Queue only (Recommended)",
        "mode_low": "Low: Daily Solo time limit",
        "daily_limit_label": "Daily Solo Limit: {minutes} mins",

        # Settings - Section 2: Night Lock
        "sec_night": " Night Curfew (DBjara Mode) ",
        "night_lock_chk": "Block game entirely during night hours (Forced Sleep)",
        "night_start": "Start:",
        "night_end": "~ End:",

        # Settings - Section 3: Lock & Startup
        "sec_lock": " Self-Control Lock (Companion OTP & Startup) ",
        "otp_chk": "Enable Companion OTP Lock (Requires OTP to change settings/exit)",
        "otp_view_btn": "Show Companion QR Code / Secret Key",
        "auto_start_chk": "Start automatically with Windows (Background Monitor)",

        # Settings - Section 4: Riot ID Validation
        "sec_riot": " Riot ID Verification (Anti-PC Cafe Bypass) ",
        "riot_desc": "Register your Riot ID to detect offline/external solo queue matches.",
        "riot_id_label": "Riot ID (Name#Tag):",

        # Settings - Section 5: Telemetry & Updates
        "sec_meta": " Analytics & Updates ",
        "telemetry_chk": "Send anonymous usage analytics (Block counts only)",
        "auto_update_chk": "Automatically check for updates on startup",
        "btn_save": "Save & Apply Settings",
        "btn_update_check": "Check for Updates",

        # OTP Auth Dialog
        "otp_auth_title": "Companion OTP Verification",
        "otp_auth_desc": "Enter the 6-digit OTP code from your companion's phone\nto modify settings or exit the app.",
        "otp_auth_btn": "Verify",
        "otp_cancel_btn": "Cancel",
        "otp_err_mismatch": "Invalid code. Please try again.",

        # OTP Setup Dialog
        "otp_setup_title": "Companion Setup (Google Authenticator) - DBjara",
        "otp_setup_head": "Register on Companion's Smartphone",
        "otp_setup_sub": "Scan this QR code with Google Authenticator on your friend's phone\nor enter the secret key manually.",
        "otp_key_title": "Secret Key:",
        "otp_copy_btn": "Copy",
        "otp_test_label": "Test with the 6-digit code generated on friend's phone:",
        "otp_test_btn": "Test & Complete Setup",
        "otp_test_empty": "Please enter a 6-digit code.",
        "otp_test_success": "Companion OTP successfully verified and registered.",
        
        # Update Dialog
        "update_found_title": "Update Found",
        "update_found_msg": "A new version ({tag}) is available!\n\nOpen download page in browser?",
        "update_latest_title": "Up to Date",
        "update_latest_msg": "You are running the latest version ({version}).",
    }
}

# 기본 언어
_CURRENT_LANG = "ko"


def set_language(lang: str):
    """현재 언어를 설정합니다 (예: 'ko', 'en')."""
    global _CURRENT_LANG
    if lang in TRANSLATIONS:
        _CURRENT_LANG = lang


def get_current_language() -> str:
    """현재 설정된 언어 코드를 반환합니다."""
    return _CURRENT_LANG


def t(key: str, lang: str = None, **kwargs) -> str:
    """
    주어진 키에 해당하는 번역된 텍스트를 반환합니다.
    인자가 주어지면 문자열 포맷팅을 수행합니다. (예: t('daily_limit_label', minutes=120))
    """
    target_lang = lang or _CURRENT_LANG
    dictionary = TRANSLATIONS.get(target_lang, TRANSLATIONS.get("ko", {}))
    text = dictionary.get(key, TRANSLATIONS["ko"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
