"""
DBjara - 다국어 지원 (i18n / Internationalization) 모듈
한국어(ko), 영어(en) 및 향후 다국어 확장을 지원하는 번역 관리 엔진입니다.
"""

from typing import Dict, Any

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ko": {
        # 앱 일반
        "app_title": "DBjara - LoL 스마트 통제 솔루션",
        "app_name": "DBjara",
        "app_sub": "친구와의 게임은 적당히, 혼자만의 밤샘 솔랭은 강력하게 통제합니다.",
        "save_success_title": "플랜 저장 완료",
        "save_success_msg": "목표 약정 및 통제 규칙이 성공적으로 저장되었습니다.",
        "copied_title": "복사 완료",
        "copied_msg": "비밀키가 클립보드에 복사되었습니다.",
        
        # 시스템 트레이
        "tray_plan_prefix": "진행 중인 플랜: ",
        "tray_plan_none": "약정 없음",
        "tray_plan_1day": "1일 데일리 플랜",
        "tray_plan_7days": "7일 주간 플랜",
        "tray_plan_30days": "30일 챌린지",
        "tray_open_settings": "설정 및 대시보드 열기",
        "tray_check_update": "업데이트 확인",
        "tray_exit": "DBjara 종료",
        
        # 알림 메시지
        "notif_night_title": "DBjara - 야간 강제 취침",
        "notif_night_msg": "야간 취침 시간대입니다. 게임이 즉시 종료되었습니다. 어서 주무세요!",
        "notif_solo_block_title": "DBjara - 솔로 큐 차단",
        "notif_solo_block_msg": "솔로 큐 상시 금지 규칙에 따라 1인 매칭이 취소되었습니다.\n(친구와 2인 이상 파티 시 플레이 가능)",
        "notif_party_block_title": "DBjara - 파티 매칭 차단",
        "notif_party_block_msg": "파티 플레이 금지 규칙으로 인해 매칭이 취소되었습니다.",
        "notif_solo_time_over_title": "DBjara - 솔로 시간 소진",
        "notif_solo_time_over_msg": "오늘의 솔로 허용 시간을 모두 소진하여 매칭이 차단되었습니다.",
        "notif_party_time_over_title": "DBjara - 파티 시간 소진",
        "notif_party_time_over_msg": "오늘의 파티 플레이 허용 시간을 모두 소진하여 매칭이 차단되었습니다.",
        "notif_cooldown_title": "DBjara - 강제 휴식 (쿨다운)",
        "notif_cooldown_msg": "게임 종료 후 {minutes}분 휴식 시간입니다! 뇌절 방지를 위해 잠시 쉬어주세요.",
        "notif_time_warn_title": "DBjara - 시간 종료 임박 (10분 전)",
        "notif_time_warn_msg": "오늘 허용된 플레이 시간이 10분 남았습니다! 이번 판이 마지막 게임입니다.",
        "notif_update_title": "DBjara 업데이트 알림",
        "notif_update_msg": "새로운 버전 ({tag})이 출시되었습니다.\n설정 창에서 확인하세요.",

        # 상단 대시보드 배너
        "dash_active_plan": "목표 약정 진행 현황",
        "dash_d_day": "D-{days}",
        "dash_today": "D-Day (오늘 종료)",
        "dash_no_plan": "자유 설정 모드",
        "dash_lock_until": "목표일: {date} 자정까지 규칙 변경 불가",
        "dash_today_usage": "오늘 사용량 ➔ 솔로: {solo_used} / 파티: {party_used}",

        # 섹션 0: 목표 약정 기간
        "sec_commitment": " 🎯 목표 약정 기간 (Commitment Plan) ",
        "plan_none": "약정 없음 (수시 변경 가능)",
        "plan_1day": "1일 플랜 (오늘 자정까지 잠금)",
        "plan_7days": "7일 작심 플랜 (1주일 잠금 - 추천 ⭐)",
        "plan_30days": "30일 갓생 챌린지 (1개월 잠금)",

        # 섹션 1: 1인 솔로 플레이 규칙
        "sec_solo": " 👤 1인 솔로 플레이 제어 ",
        "solo_block_always": "상시 전면 차단 (1인 큐 절대 불가 - 권장 ⭐)",
        "solo_time_limit": "일일 솔로 시간 제한:",
        "solo_unlimited": "제한 없음 (솔로 플레이 자유 허용)",

        # 섹션 2: 2인 이상 다인큐 규칙
        "sec_party": " 👥 2인 이상 다인큐(파티) 제어 ",
        "party_unlimited": "무제한 허용 (친구와의 게임은 자유)",
        "party_time_limit": "일일 파티 시간 제한:",
        "party_block_always": "파티도 전면 차단 (게임 완전 금지)",

        # 섹션 3: 야간 취침 모드
        "sec_night": " 🌙 야간 강제 취침 모드 (디비자라) ",
        "night_lock_chk": "설정 시간대 게임 완전 차단 (동반자 무관 강제 종료)",
        "night_start": "차단 시작:",
        "night_end": "~ 종료:",

        # 섹션 4: 스마트 미세조정 (추가 스마트 통제)
        "sec_smart": " ⚡ 스마트 멘탈 & 쿨다운 통제 ",
        "cooldown_chk": "게임 종료 후 5분 강제 휴식 타이머 (연승/연패 뇌절 및 연속 게임 방지)",

        # 섹션 5: 자제력 자물쇠 & 보안
        "sec_lock": " 🔒 자제력 자물쇠 & 보안 설정 ",
        "otp_chk": "동반자 OTP 자물쇠 활성화 (잠금 기간 중 수정 시 OTP 요구)",
        "otp_view_btn": "동반자 등록 QR / 비밀키 보기",
        "auto_start_chk": "윈도우 부팅 시 자동 실행 (백그라운드 상시 감시)",

        # 섹션 6: 부가 기능 & 익명 통계
        "sec_meta": " 🔍 부가 기능 및 전적 검증 (로그 수집) ",
        "riot_desc": "소환사 Riot ID 등록 (외부/PC방 몰래 솔랭 감지):",
        "telemetry_chk": "익명 사용 통계 수집 동의 (차단 횟수 등 비식별 데이터)",
        "auto_update_chk": "시작 시 최신 버전 자동 확인",
        "btn_save": "플랜 저장 및 통제 시작",
        "btn_update_check": "업데이트 확인",

        # OTP 모달
        "otp_auth_title": "보안 인증 (약정 기간 잠금 해제)",
        "otp_auth_desc": "설정을 변경하려면 동반자 OTP 번호(6자리)\n또는 비상 인증 코드를 입력하세요.",
        "otp_auth_btn": "잠금 해제 및 인증",
        "otp_cancel_btn": "취소",
        "otp_err_mismatch": "인증번호가 일치하지 않습니다.",

        # OTP 등록 팝업
        "otp_setup_title": "동반자 등록 (Google Authenticator) - DBjara",
        "otp_setup_head": "동반자(친구/가족) 스마트폰 등록",
        "otp_setup_sub": "친구의 스마트폰(Google Authenticator 등)으로\n아래 QR 코드를 스캔하거나 비밀키를 직접 입력해 등록하세요.",
        "otp_key_title": "등록용 비밀키(Secret Key):",
        "otp_copy_btn": "복사",
        "otp_test_label": "등록 후 친구 폰의 6자리 번호로 테스트:",
        "otp_test_btn": "테스트 및 등록 완료",
        "otp_test_empty": "6자리 번호를 입력해주세요.",
        "otp_test_success": "동반자 OTP가 정상 등록되었습니다.",
        
        # 업데이트 팝업
        "update_found_title": "새 버전 발견",
        "update_found_msg": "새로운 버전 ({tag})이 출시되었습니다.\n\n다운로드 페이지를 여시겠습니까?",
        "update_latest_title": "최신 버전",
        "update_latest_msg": "현재 최신 버전({version})을 사용 중입니다.",
    },
    "en": {
        # General
        "app_title": "DBjara - Smart LoL Control Solution",
        "app_name": "DBjara",
        "app_sub": "Enjoy casual games with friends, strictly eliminate late-night solo queue bingeing.",
        "save_success_title": "Plan Saved",
        "save_success_msg": "Commitment plan and control rules have been successfully applied.",
        "copied_title": "Copied",
        "copied_msg": "Secret key copied to clipboard.",
        
        # System Tray
        "tray_plan_prefix": "Active Plan: ",
        "tray_plan_none": "No Commitment",
        "tray_plan_1day": "1-Day Daily Plan",
        "tray_plan_7days": "7-Day Weekly Plan",
        "tray_plan_30days": "30-Day Challenge",
        "tray_open_settings": "Open Settings & Dashboard",
        "tray_check_update": "Check for Updates",
        "tray_exit": "Exit DBjara",
        
        # Notifications
        "notif_night_title": "DBjara - Night Curfew",
        "notif_night_msg": "Night sleep curfew active. League client closed. Go to sleep!",
        "notif_solo_block_title": "DBjara - Solo Queue Blocked",
        "notif_solo_block_msg": "Solo queue is strictly blocked. Matchmaking canceled.\n(Only party queue with friends is allowed)",
        "notif_party_block_title": "DBjara - Party Queue Blocked",
        "notif_party_block_msg": "Party play is disabled under current rule. Matchmaking canceled.",
        "notif_solo_time_over_title": "DBjara - Solo Limit Reached",
        "notif_solo_time_over_msg": "Daily solo time limit exhausted. Matchmaking blocked.",
        "notif_party_time_over_title": "DBjara - Party Limit Reached",
        "notif_party_time_over_msg": "Daily party time limit exhausted. Matchmaking blocked.",
        "notif_cooldown_title": "DBjara - Rest Cooldown",
        "notif_cooldown_msg": "Post-game mandatory rest time ({minutes}m)! Please take a short break.",
        "notif_time_warn_title": "DBjara - Time Warning (10 mins left)",
        "notif_time_warn_msg": "You have 10 minutes left of play time today! This is your final game.",
        "notif_update_title": "DBjara Update Available",
        "notif_update_msg": "New version ({tag}) is available!\nCheck settings to download.",

        # Dashboard Banner
        "dash_active_plan": "Commitment Plan Status",
        "dash_d_day": "D-{days}",
        "dash_today": "D-Day (Ends Today)",
        "dash_no_plan": "Flexible Rule Mode",
        "dash_lock_until": "Locked until midnight ({date})",
        "dash_today_usage": "Today's Usage ➔ Solo: {solo_used} / Party: {party_used}",

        # Section 0: Commitment Plan
        "sec_commitment": " 🎯 Commitment Plan ",
        "plan_none": "No Plan (Flexible changes anytime)",
        "plan_1day": "1-Day Plan (Locked until midnight)",
        "plan_7days": "7-Day Plan (Locked for 1 week - Recommended ⭐)",
        "plan_30days": "30-Day Challenge (Locked for 1 month)",

        # Section 1: Solo Rules
        "sec_solo": " 👤 Solo Play Control ",
        "solo_block_always": "Always Block Solo Queue (Recommended ⭐)",
        "solo_time_limit": "Daily Solo Time Limit:",
        "solo_unlimited": "Unlimited (Allow solo queue freely)",

        # Section 2: Party Rules
        "sec_party": " 👥 Party (2+ Players) Control ",
        "party_unlimited": "Unlimited (Enjoy games with friends freely)",
        "party_time_limit": "Daily Party Time Limit:",
        "party_block_always": "Block Party Play entirely (Total game ban)",

        # Section 3: Night Curfew
        "sec_night": " 🌙 Night Sleep Curfew (DBjara Mode) ",
        "night_lock_chk": "Block game entirely during night hours (Forced Sleep)",
        "night_start": "Start:",
        "night_end": "~ End:",

        # Section 4: Smart Cooldown
        "sec_smart": " ⚡ Smart Rest & Cooldown Control ",
        "cooldown_chk": "Mandatory 5-minute cooldown after each match (Anti-binge gaming)",

        # Section 5: Lock & Security
        "sec_lock": " 🔒 Commitment Lock & Security ",
        "otp_chk": "Enable Companion OTP Lock (Requires OTP to edit locked plan)",
        "otp_view_btn": "Show Companion QR Code / Secret Key",
        "auto_start_chk": "Start automatically with Windows (Background Monitor)",

        # Section 6: Verification & Analytics
        "sec_meta": " 🔍 Verification & Anonymous Analytics ",
        "riot_desc": "Riot ID (Anti-PC Cafe Bypass):",
        "telemetry_chk": "Send anonymous usage analytics (Block counts only)",
        "auto_update_chk": "Check for updates on startup",
        "btn_save": "Save Plan & Start Enforcement",
        "btn_update_check": "Check for Updates",

        # OTP Modal
        "otp_auth_title": "Security Verification (Unlock Plan)",
        "otp_auth_desc": "Enter companion OTP (6 digits)\nor Emergency Master Code to modify settings.",
        "otp_auth_btn": "Unlock & Verify",
        "otp_cancel_btn": "Cancel",
        "otp_err_mismatch": "Invalid verification code.",

        # OTP Setup
        "otp_setup_title": "Companion Setup (Google Authenticator) - DBjara",
        "otp_setup_head": "Register on Companion's Smartphone",
        "otp_setup_sub": "Scan this QR code with Google Authenticator on your friend's phone\nor enter the secret key manually.",
        "otp_key_title": "Secret Key:",
        "otp_copy_btn": "Copy",
        "otp_test_label": "Test with 6-digit code on friend's phone:",
        "otp_test_btn": "Test & Complete Setup",
        "otp_test_empty": "Please enter a 6-digit code.",
        "otp_test_success": "Companion OTP registered successfully.",
        
        # Update Dialog
        "update_found_title": "Update Found",
        "update_found_msg": "A new version ({tag}) is available!\n\nOpen download page in browser?",
        "update_latest_title": "Up to Date",
        "update_latest_msg": "You are running the latest version ({version}).",
    }
}

_CURRENT_LANG = "ko"


def set_language(lang: str):
    global _CURRENT_LANG
    if lang in TRANSLATIONS:
        _CURRENT_LANG = lang


def get_current_language() -> str:
    return _CURRENT_LANG


def t(key: str, lang: str = None, **kwargs) -> str:
    target_lang = lang or _CURRENT_LANG
    dictionary = TRANSLATIONS.get(target_lang, TRANSLATIONS.get("ko", {}))
    text = dictionary.get(key, TRANSLATIONS["ko"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
