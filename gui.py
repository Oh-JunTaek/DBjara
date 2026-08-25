"""
DBjara 2.0 - 모던 슬레이트 & 인디고 테마 GUI
복합 룰셋(솔로/파티/야간 교집합 제어) 및 목표 약정 기간(Commitment Plan) 시스템을 제공합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
from typing import Optional, Callable

from config import (
    load_config, save_config, set_auto_start,
    calculate_commitment_end_date, is_commitment_locked, get_remaining_days
)
from totp import generate_secret, verify_totp, get_otpauth_uri
from updater import get_latest_version_info, open_release_page, CURRENT_VERSION
from i18n import t, set_language, get_current_language

try:
    import qrcode
    from PIL import Image, ImageTk
    HAS_QR = True
except ImportError:
    HAS_QR = False


class SlateTheme:
    """모던 슬레이트 & 인디고(Slate & Indigo) 테마 팔레트"""
    BG_DARK = "#0f172a"        # 딥 슬레이트 네이비 (메인 배경)
    BG_CARD = "#1e293b"        # 부드러운 다크 차콜 (카드 섹션)
    BG_CARD_LIGHT = "#334155"  # 슬레이트 그레이 (컨트롤/인풋 배경)
    BG_CARD_HOVER = "#475569"  # 호버 상태

    ACCENT_CYAN = "#38bdf8"    # 일렉트릭 사이언 (메인 포인트)
    ACCENT_INDIGO = "#818cf8"  # 인디고 바이올렛 (배지 / 헤더)
    ACCENT_EMERALD = "#10b981" # 에메랄드 그린 (안전/성공)
    ACCENT_ROSE = "#f43f5e"    # 로즈 레드 (차단/경고)

    TEXT_MAIN = "#f8fafc"      # 퓨어 화이트 (가독성 최상)
    TEXT_MUTED = "#94a3b8"     # 차분한 쿨 그레이
    TEXT_SUBTLE = "#64748b"    # 보조 텍스트

    BORDER = "#334155"         # 테두리
    BORDER_ACTIVE = "#818cf8"  # 활성 테두리


class OTPAuthDialog(tk.Toplevel):
    """동반자 OTP 번호(6자리) 또는 비상 마스터키(1234) 입력을 요구하는 모달 창입니다."""

    def __init__(self, parent, secret: str, on_success: Callable[[], None]):
        super().__init__(parent)
        self.secret = secret
        self.on_success = on_success
        self.title(t("otp_auth_title"))
        self.geometry("440x310")
        self.resizable(False, False)
        self.configure(bg=SlateTheme.BG_DARK)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        pad = tk.Frame(self, bg=SlateTheme.BG_DARK, padx=26, pady=22)
        pad.pack(fill=tk.BOTH, expand=True)

        lbl_title = tk.Label(
            pad, text=t("otp_auth_title"), font=("Malgun Gothic", 14, "bold"),
            bg=SlateTheme.BG_DARK, fg=SlateTheme.TEXT_MAIN
        )
        lbl_title.pack(pady=(0, 6))

        lbl_desc = tk.Label(
            pad, text=t("otp_auth_desc"), font=("Malgun Gothic", 10),
            bg=SlateTheme.BG_DARK, fg=SlateTheme.TEXT_MUTED, justify=tk.CENTER
        )
        lbl_desc.pack(pady=6)

        self.entry_otp = tk.Entry(
            pad, font=("Consolas", 20, "bold"), justify=tk.CENTER,
            bg=SlateTheme.BG_CARD_LIGHT, fg=SlateTheme.TEXT_MAIN,
            insertbackground=SlateTheme.TEXT_MAIN, bd=0, highlightthickness=1,
            highlightcolor=SlateTheme.ACCENT_CYAN, highlightbackground=SlateTheme.BORDER
        )
        self.entry_otp.pack(ipady=6, fill=tk.X, pady=8)
        self.entry_otp.focus_set()
        self.entry_otp.bind("<Return>", lambda e: self.verify())

        self.lbl_error = tk.Label(
            pad, text="", font=("Malgun Gothic", 9, "bold"), bg=SlateTheme.BG_DARK, fg=SlateTheme.ACCENT_ROSE
        )
        self.lbl_error.pack(pady=(0, 6))

        btn_frame = tk.Frame(pad, bg=SlateTheme.BG_DARK)
        btn_frame.pack(fill=tk.X)

        btn_submit = tk.Button(
            btn_frame, text=t("otp_auth_btn"), font=("Malgun Gothic", 11, "bold"),
            bg=SlateTheme.ACCENT_CYAN, fg=SlateTheme.BG_DARK, activebackground="#0284c7",
            activeforeground="white", bd=0, relief=tk.FLAT, pady=7, cursor="hand2",
            command=self.verify
        )
        btn_submit.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        btn_cancel = tk.Button(
            btn_frame, text=t("otp_cancel_btn"), font=("Malgun Gothic", 11),
            bg=SlateTheme.BG_CARD_LIGHT, fg=SlateTheme.TEXT_MUTED, bd=0, relief=tk.FLAT,
            pady=7, cursor="hand2", command=self.destroy
        )
        btn_cancel.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

    def verify(self):
        code = self.entry_otp.get().strip()
        # 개발/비상용 마스터키 1234 우선 검증
        if code == "1234":
            self.destroy()
            self.on_success()
            return

        # 동반자 OTP 검증
        if self.secret and verify_totp(self.secret, code):
            self.destroy()
            self.on_success()
        else:
            self.lbl_error.config(text=t("otp_err_mismatch"))
            self.entry_otp.delete(0, tk.END)


class OTPSetupDialog(tk.Toplevel):
    """동반자 스마트폰 등록을 위한 비밀키 및 QR 코드를 표시하는 대화상자입니다."""

    def __init__(self, parent, current_secret: str, on_complete: Callable[[str], None]):
        super().__init__(parent)
        self.secret = current_secret if current_secret else generate_secret()
        self.on_complete = on_complete
        self.title(t("otp_setup_title"))
        self.geometry("480x600")
        self.resizable(False, False)
        self.configure(bg=SlateTheme.BG_DARK)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        pad = tk.Frame(self, bg=SlateTheme.BG_DARK, padx=24, pady=20)
        pad.pack(fill=tk.BOTH, expand=True)

        lbl_title = tk.Label(
            pad, text=t("otp_setup_head"), font=("Malgun Gothic", 14, "bold"),
            bg=SlateTheme.BG_DARK, fg=SlateTheme.TEXT_MAIN
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            pad, text=t("otp_setup_sub"), font=("Malgun Gothic", 10),
            bg=SlateTheme.BG_DARK, fg=SlateTheme.TEXT_MUTED, justify=tk.LEFT
        )
        lbl_sub.pack(anchor="w", pady=(4, 12))

        # QR 코드 표시 영역
        qr_frame = tk.Frame(pad, bg=SlateTheme.BG_CARD, bd=1, relief=tk.FLAT, padx=10, pady=10)
        qr_frame.pack(pady=4)

        if HAS_QR:
            uri = get_otpauth_uri(self.secret)
            qr = qrcode.QRCode(box_size=4, border=2)
            qr.add_data(uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            self.tk_img = ImageTk.PhotoImage(img)
            qr_label = tk.Label(qr_frame, image=self.tk_img, bg="white")
            qr_label.pack()
        else:
            lbl_no_qr = tk.Label(
                qr_frame, text="[QR Module Error] Secret Key Only",
                bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MUTED, font=("Malgun Gothic", 10), pady=30, padx=20
            )
            lbl_no_qr.pack()

        # 비밀키 표시 및 복사 버튼
        key_box = tk.Frame(pad, bg=SlateTheme.BG_CARD_LIGHT, padx=12, pady=8)
        key_box.pack(fill=tk.X, pady=12)

        lbl_key_title = tk.Label(key_box, text=t("otp_key_title"), font=("Malgun Gothic", 9), bg=SlateTheme.BG_CARD_LIGHT, fg=SlateTheme.TEXT_MUTED)
        lbl_key_title.pack(anchor="w")

        key_row = tk.Frame(key_box, bg=SlateTheme.BG_CARD_LIGHT)
        key_row.pack(fill=tk.X, pady=2)

        self.lbl_secret = tk.Label(
            key_row, text=self.secret, font=("Consolas", 14, "bold"),
            bg=SlateTheme.BG_CARD_LIGHT, fg=SlateTheme.ACCENT_CYAN
        )
        self.lbl_secret.pack(side=tk.LEFT)

        btn_copy = tk.Button(
            key_row, text=t("otp_copy_btn"), font=("Malgun Gothic", 9, "bold"),
            bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MAIN, bd=0, padx=10, pady=3,
            cursor="hand2", command=self.copy_key
        )
        btn_copy.pack(side=tk.RIGHT)

        # 등록 검증 테스트 필드
        lbl_test = tk.Label(
            pad, text=t("otp_test_label"),
            font=("Malgun Gothic", 10), bg=SlateTheme.BG_DARK, fg=SlateTheme.TEXT_MAIN
        )
        lbl_test.pack(anchor="w", pady=(6, 2))

        test_row = tk.Frame(pad, bg=SlateTheme.BG_DARK)
        test_row.pack(fill=tk.X, pady=2)

        self.entry_test = tk.Entry(
            test_row, font=("Consolas", 14, "bold"), justify=tk.CENTER,
            bg=SlateTheme.BG_CARD_LIGHT, fg=SlateTheme.TEXT_MAIN,
            insertbackground=SlateTheme.TEXT_MAIN, bd=0, highlightthickness=1,
            highlightcolor=SlateTheme.ACCENT_CYAN, highlightbackground=SlateTheme.BORDER, width=10
        )
        self.entry_test.pack(side=tk.LEFT, ipady=4)

        btn_test = tk.Button(
            test_row, text=t("otp_test_btn"), font=("Malgun Gothic", 10, "bold"),
            bg=SlateTheme.ACCENT_CYAN, fg=SlateTheme.BG_DARK, bd=0, padx=14, pady=5,
            cursor="hand2", command=self.test_and_save
        )
        btn_test.pack(side=tk.LEFT, padx=8)

        self.lbl_msg = tk.Label(pad, text="", font=("Malgun Gothic", 10, "bold"), bg=SlateTheme.BG_DARK)
        self.lbl_msg.pack(pady=4)

    def copy_key(self):
        self.clipboard_clear()
        self.clipboard_append(self.secret)
        messagebox.showinfo(t("copied_title"), t("copied_msg"), parent=self)

    def test_and_save(self):
        code = self.entry_test.get().strip()
        if not code:
            self.lbl_msg.config(text=t("otp_test_empty"), fg=SlateTheme.ACCENT_ROSE)
            return

        if code == "1234" or verify_totp(self.secret, code):
            messagebox.showinfo(t("save_success_title"), t("otp_test_success"), parent=self)
            self.destroy()
            self.on_complete(self.secret)
        else:
            self.lbl_msg.config(text=t("otp_err_mismatch"), fg=SlateTheme.ACCENT_ROSE)


class SettingsWindow(tk.Tk):
    """DBjara 2.0 스마트 대시보드 및 복합 룰 설정 창"""

    TIME_OPTIONS = [
        ("30분 (0.5시간)", 30),
        ("60분 (1시간)", 60),
        ("90분 (1.5시간)", 90),
        ("120분 (2시간)", 120),
        ("150분 (2.5시간)", 150),
        ("180분 (3시간)", 180),
        ("210분 (3.5시간)", 210),
        ("240분 (4시간)", 240),
    ]

    NIGHT_START_OPTIONS = ["22:00", "22:30", "23:00", "23:30", "00:00"]
    NIGHT_END_OPTIONS = ["05:00", "05:30", "06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:00"]

    def __init__(self, on_config_updated: Optional[Callable[[dict], None]] = None):
        super().__init__()
        self.on_config_updated = on_config_updated
        self.config = load_config()

        self.title(t("app_title"))
        self.geometry("620x920")
        self.resizable(False, False)
        self.configure(bg=SlateTheme.BG_DARK)

        self._init_variables()
        self.main_container = None
        self._build_ui()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _init_variables(self):
        self.var_lang = tk.StringVar(value=self.config.get("language", "ko"))
        self.var_commitment = tk.StringVar(value=self.config.get("commitment_plan", "none"))
        
        self.var_solo_rule = tk.StringVar(value=self.config.get("solo_rule", "block_always"))
        self.var_solo_limit = tk.IntVar(value=self.config.get("solo_limit_minutes", 60))
        
        self.var_party_rule = tk.StringVar(value=self.config.get("party_rule", "time_limit"))
        self.var_party_limit = tk.IntVar(value=self.config.get("party_limit_minutes", 120))
        
        self.var_night_lock = tk.BooleanVar(value=self.config.get("night_lock", True))
        
        n_start = self.config.get("night_start", "23:00")
        if n_start == "24:00":
            n_start = "00:00"
        self.var_night_start = tk.StringVar(value=n_start)
        self.var_night_end = tk.StringVar(value=self.config.get("night_end", "07:00"))
        
        self.var_otp_enabled = tk.BooleanVar(value=self.config.get("otp_enabled", False))
        self.var_auto_start = tk.BooleanVar(value=self.config.get("auto_start", False))
        self.var_riot_id = tk.StringVar(value=self.config.get("riot_id", ""))
        self.var_riot_key = tk.StringVar(value=self.config.get("riot_api_key", ""))
        self.var_telemetry = tk.BooleanVar(value=self.config.get("telemetry_enabled", True))
        self.var_auto_update = tk.BooleanVar(value=self.config.get("auto_update_check", True))
        self.otp_secret = self.config.get("otp_secret", "")

    def _build_ui(self):
        if self.main_container:
            self.main_container.destroy()

        self.title(t("app_title"))
        self.main_container = tk.Frame(self, bg=SlateTheme.BG_DARK, padx=22, pady=16)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # 1. 상단 타이틀 바 & 언어 / 업데이트
        head = tk.Frame(self.main_container, bg=SlateTheme.BG_DARK)
        head.pack(fill=tk.X, pady=(0, 10))

        title_row = tk.Frame(head, bg=SlateTheme.BG_DARK)
        title_row.pack(fill=tk.X)

        title = tk.Label(
            title_row, text=t("app_name"), font=("Malgun Gothic", 17, "bold"),
            bg=SlateTheme.BG_DARK, fg=SlateTheme.TEXT_MAIN
        )
        title.pack(side=tk.LEFT)

        lbl_ver = tk.Label(
            title_row, text=f"{CURRENT_VERSION}", font=("Consolas", 10, "bold"),
            bg=SlateTheme.BG_CARD_LIGHT, fg=SlateTheme.ACCENT_CYAN, padx=8, pady=2
        )
        lbl_ver.pack(side=tk.LEFT, padx=10)

        # 언어 선택기
        lang_frame = tk.Frame(title_row, bg=SlateTheme.BG_DARK)
        lang_frame.pack(side=tk.RIGHT)

        lbl_l = tk.Label(lang_frame, text="🌐", font=("Segoe UI Emoji", 11), bg=SlateTheme.BG_DARK, fg=SlateTheme.TEXT_MUTED)
        lbl_l.pack(side=tk.LEFT, padx=(0, 4))

        cb_lang = ttk.Combobox(
            lang_frame, textvariable=self.var_lang, values=["ko", "en"],
            state="readonly", width=6, font=("Malgun Gothic", 10)
        )
        cb_lang.pack(side=tk.LEFT)
        cb_lang.bind("<<ComboboxSelected>>", self._on_language_changed)

        btn_update = tk.Button(
            title_row, text=t("btn_update_check"), font=("Malgun Gothic", 9, "bold"),
            bg=SlateTheme.BG_CARD_LIGHT, fg=SlateTheme.TEXT_MAIN, bd=0, padx=8, pady=3,
            cursor="hand2", command=self.check_update_manual
        )
        btn_update.pack(side=tk.RIGHT, padx=8)

        sub = tk.Label(
            head, text=t("app_sub"), font=("Malgun Gothic", 9),
            bg=SlateTheme.BG_DARK, fg=SlateTheme.TEXT_MUTED
        )
        sub.pack(anchor="w", pady=(2, 0))

        # 2. 상단 D-Day 대시보드 상태 배너 카드
        self._build_dashboard_banner()

        # 3. 섹션 0: 목표 약정 기간 (Commitment Plan)
        card_commit = tk.LabelFrame(
            self.main_container, text=t("sec_commitment"), font=("Malgun Gothic", 10, "bold"),
            bg=SlateTheme.BG_CARD, fg=SlateTheme.ACCENT_INDIGO, bd=1, relief=tk.SOLID, padx=14, pady=6
        )
        card_commit.pack(fill=tk.X, pady=(0, 8))

        plan_frame = tk.Frame(card_commit, bg=SlateTheme.BG_CARD)
        plan_frame.pack(fill=tk.X, pady=2)

        plans = [
            ("plan_none", "none"),
            ("plan_1day", "1day"),
            ("plan_7days", "7days"),
            ("plan_30days", "30days"),
        ]
        for key, val in plans:
            rb = tk.Radiobutton(
                plan_frame, text=t(key), variable=self.var_commitment, value=val,
                font=("Malgun Gothic", 9, "bold" if val != "none" else "normal"),
                bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MAIN,
                selectcolor=SlateTheme.BG_CARD_LIGHT, activebackground=SlateTheme.BG_CARD,
                activeforeground=SlateTheme.TEXT_MAIN
            )
            rb.pack(anchor="w", pady=1)

        # 4. 섹션 1: 1인 솔로 플레이 제어 (전면 차단 vs 시간 제한 vs 무제한)
        card_solo = tk.LabelFrame(
            self.main_container, text=t("sec_solo"), font=("Malgun Gothic", 10, "bold"),
            bg=SlateTheme.BG_CARD, fg=SlateTheme.ACCENT_CYAN, bd=1, relief=tk.SOLID, padx=14, pady=6
        )
        card_solo.pack(fill=tk.X, pady=(0, 8))

        r_s1 = tk.Radiobutton(
            card_solo, text=t("solo_block_always"), variable=self.var_solo_rule, value="block_always",
            font=("Malgun Gothic", 9, "bold"), bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MAIN,
            selectcolor=SlateTheme.BG_CARD_LIGHT, activebackground=SlateTheme.BG_CARD,
            activeforeground=SlateTheme.TEXT_MAIN, command=self._on_solo_rule_change
        )
        r_s1.pack(anchor="w", pady=1)

        row_s2 = tk.Frame(card_solo, bg=SlateTheme.BG_CARD)
        row_s2.pack(fill=tk.X, pady=1)

        r_s2 = tk.Radiobutton(
            row_s2, text=t("solo_time_limit"), variable=self.var_solo_rule, value="time_limit",
            font=("Malgun Gothic", 9, "bold"), bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MAIN,
            selectcolor=SlateTheme.BG_CARD_LIGHT, activebackground=SlateTheme.BG_CARD,
            activeforeground=SlateTheme.TEXT_MAIN, command=self._on_solo_rule_change
        )
        r_s2.pack(side=tk.LEFT)

        self.cb_solo_time = ttk.Combobox(
            row_s2, values=[item[0] for item in self.TIME_OPTIONS], state="readonly", width=14, font=("Malgun Gothic", 9)
        )
        self._sync_combobox(self.cb_solo_time, self.var_solo_limit.get())
        self.cb_solo_time.pack(side=tk.LEFT, padx=6)
        self.cb_solo_time.bind("<<ComboboxSelected>>", lambda e: self._on_time_selected(self.cb_solo_time, self.var_solo_limit))

        r_s3 = tk.Radiobutton(
            card_solo, text=t("solo_unlimited"), variable=self.var_solo_rule, value="unlimited",
            font=("Malgun Gothic", 9), bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MUTED,
            selectcolor=SlateTheme.BG_CARD_LIGHT, activebackground=SlateTheme.BG_CARD,
            activeforeground=SlateTheme.TEXT_MAIN, command=self._on_solo_rule_change
        )
        r_s3.pack(anchor="w", pady=1)
        self._on_solo_rule_change()

        # 5. 섹션 2: 2인 이상 다인큐(파티) 제어 (무제한 vs 시간 제한 vs 전면 차단)
        card_party = tk.LabelFrame(
            self.main_container, text=t("sec_party"), font=("Malgun Gothic", 10, "bold"),
            bg=SlateTheme.BG_CARD, fg=SlateTheme.ACCENT_EMERALD, bd=1, relief=tk.SOLID, padx=14, pady=6
        )
        card_party.pack(fill=tk.X, pady=(0, 8))

        r_p1 = tk.Radiobutton(
            card_party, text=t("party_unlimited"), variable=self.var_party_rule, value="unlimited",
            font=("Malgun Gothic", 9), bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MAIN,
            selectcolor=SlateTheme.BG_CARD_LIGHT, activebackground=SlateTheme.BG_CARD,
            activeforeground=SlateTheme.TEXT_MAIN, command=self._on_party_rule_change
        )
        r_p1.pack(anchor="w", pady=1)

        row_p2 = tk.Frame(card_party, bg=SlateTheme.BG_CARD)
        row_p2.pack(fill=tk.X, pady=1)

        r_p2 = tk.Radiobutton(
            row_p2, text=t("party_time_limit"), variable=self.var_party_rule, value="time_limit",
            font=("Malgun Gothic", 9, "bold"), bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MAIN,
            selectcolor=SlateTheme.BG_CARD_LIGHT, activebackground=SlateTheme.BG_CARD,
            activeforeground=SlateTheme.TEXT_MAIN, command=self._on_party_rule_change
        )
        r_p2.pack(side=tk.LEFT)

        self.cb_party_time = ttk.Combobox(
            row_p2, values=[item[0] for item in self.TIME_OPTIONS], state="readonly", width=14, font=("Malgun Gothic", 9)
        )
        self._sync_combobox(self.cb_party_time, self.var_party_limit.get())
        self.cb_party_time.pack(side=tk.LEFT, padx=6)
        self.cb_party_time.bind("<<ComboboxSelected>>", lambda e: self._on_time_selected(self.cb_party_time, self.var_party_limit))

        r_p3 = tk.Radiobutton(
            card_party, text=t("party_block_always"), variable=self.var_party_rule, value="block_always",
            font=("Malgun Gothic", 9, "bold"), bg=SlateTheme.BG_CARD, fg=SlateTheme.ACCENT_ROSE,
            selectcolor=SlateTheme.BG_CARD_LIGHT, activebackground=SlateTheme.BG_CARD,
            activeforeground=SlateTheme.TEXT_MAIN, command=self._on_party_rule_change
        )
        r_p3.pack(anchor="w", pady=1)
        self._on_party_rule_change()

        # 6. 섹션 3: 야간 시간 강제 차단
        card_night = tk.LabelFrame(
            self.main_container, text=t("sec_night"), font=("Malgun Gothic", 10, "bold"),
            bg=SlateTheme.BG_CARD, fg=SlateTheme.ACCENT_ROSE, bd=1, relief=tk.SOLID, padx=14, pady=6
        )
        card_night.pack(fill=tk.X, pady=(0, 8))

        chk_night = tk.Checkbutton(
            card_night, text=t("night_lock_chk"), variable=self.var_night_lock,
            font=("Malgun Gothic", 9, "bold"), bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MAIN,
            selectcolor=SlateTheme.BG_CARD_LIGHT, activebackground=SlateTheme.BG_CARD,
            activeforeground=SlateTheme.TEXT_MAIN
        )
        chk_night.pack(anchor="w")

        time_row = tk.Frame(card_night, bg=SlateTheme.BG_CARD)
        time_row.pack(fill=tk.X, pady=(4, 2), padx=14)

        lbl_t1 = tk.Label(time_row, text=t("night_start"), font=("Malgun Gothic", 9), bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MUTED)
        lbl_t1.pack(side=tk.LEFT)

        cb_n_start = ttk.Combobox(
            time_row, textvariable=self.var_night_start, values=self.NIGHT_START_OPTIONS,
            state="readonly", width=7, font=("Malgun Gothic", 9)
        )
        cb_n_start.pack(side=tk.LEFT, padx=6)

        lbl_t2 = tk.Label(time_row, text=t("night_end"), font=("Malgun Gothic", 9), bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MUTED)
        lbl_t2.pack(side=tk.LEFT, padx=(10, 0))

        cb_n_end = ttk.Combobox(
            time_row, textvariable=self.var_night_end, values=self.NIGHT_END_OPTIONS,
            state="readonly", width=7, font=("Malgun Gothic", 9)
        )
        cb_n_end.pack(side=tk.LEFT, padx=6)

        # 7. 섹션 4: 자제력 자물쇠 & OTP / 마스터키
        card_lock = tk.LabelFrame(
            self.main_container, text=t("sec_lock"), font=("Malgun Gothic", 10, "bold"),
            bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MAIN, bd=1, relief=tk.SOLID, padx=14, pady=6
        )
        card_lock.pack(fill=tk.X, pady=(0, 8))

        chk_otp = tk.Checkbutton(
            card_lock, text=t("otp_chk"), variable=self.var_otp_enabled,
            font=("Malgun Gothic", 9), bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MAIN,
            selectcolor=SlateTheme.BG_CARD_LIGHT, activebackground=SlateTheme.BG_CARD,
            activeforeground=SlateTheme.TEXT_MAIN, command=self._on_otp_toggle
        )
        chk_otp.pack(anchor="w")

        row_otp = tk.Frame(card_lock, bg=SlateTheme.BG_CARD)
        row_otp.pack(fill=tk.X, padx=14, pady=(2, 3))

        btn_otp_setup = tk.Button(
            row_otp, text=t("otp_view_btn"), font=("Malgun Gothic", 8, "bold"),
            bg=SlateTheme.BG_CARD_LIGHT, fg=SlateTheme.TEXT_MAIN, bd=0, padx=8, pady=3,
            cursor="hand2", command=self.open_otp_setup
        )
        btn_otp_setup.pack(side=tk.LEFT)

        lbl_master_hint = tk.Label(
            row_otp, text=t("master_key_hint"), font=("Malgun Gothic", 8),
            bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_SUBTLE
        )
        lbl_master_hint.pack(side=tk.LEFT, padx=10)

        chk_auto = tk.Checkbutton(
            card_lock, text=t("auto_start_chk"), variable=self.var_auto_start,
            font=("Malgun Gothic", 9), bg=SlateTheme.BG_CARD, fg=SlateTheme.TEXT_MAIN,
            selectcolor=SlateTheme.BG_CARD_LIGHT, activebackground=SlateTheme.BG_CARD,
            activeforeground=SlateTheme.TEXT_MAIN
        )
        chk_auto.pack(anchor="w")

        # 8. 저장 버튼
        btn_save = tk.Button(
            self.main_container, text=t("btn_save"), font=("Malgun Gothic", 12, "bold"),
            bg=SlateTheme.ACCENT_CYAN, fg=SlateTheme.BG_DARK, activebackground="#0284c7",
            activeforeground="white", bd=0, relief=tk.FLAT, pady=9, cursor="hand2",
            command=self.request_save
        )
        btn_save.pack(fill=tk.X, pady=(6, 0))

    def _build_dashboard_banner(self):
        """상단 D-Day 상태 및 약정 현황 배너 렌더링"""
        is_locked = is_commitment_locked(self.config)
        rem_days = get_remaining_days(self.config)
        end_date = self.config.get("commitment_end_date", "")

        banner = tk.Frame(
            self.main_container, bg=SlateTheme.BG_CARD_LIGHT,
            padx=14, pady=10, bd=1, relief=tk.SOLID
        )
        banner.pack(fill=tk.X, pady=(0, 10))

        top_row = tk.Frame(banner, bg=SlateTheme.BG_CARD_LIGHT)
        top_row.pack(fill=tk.X)

        if is_locked:
            d_text = t("dash_today") if rem_days == 0 else t("dash_d_day", days=rem_days)
            badge_color = SlateTheme.ACCENT_ROSE if rem_days == 0 else SlateTheme.ACCENT_INDIGO

            lbl_badge = tk.Label(
                top_row, text=f" 🔒 {d_text} ", font=("Malgun Gothic", 10, "bold"),
                bg=badge_color, fg="white", padx=6, pady=2
            )
            lbl_badge.pack(side=tk.LEFT)

            plan_name = self.config.get("commitment_plan", "custom")
            lbl_status = tk.Label(
                top_row, text=f" [{t('plan_' + plan_name)}] {t('dash_lock_until', date=end_date.split()[0])}",
                font=("Malgun Gothic", 9.5, "bold"), bg=SlateTheme.BG_CARD_LIGHT, fg=SlateTheme.TEXT_MAIN
            )
            lbl_status.pack(side=tk.LEFT, padx=8)
        else:
            lbl_badge = tk.Label(
                top_row, text=f" 🔓 {t('dash_no_plan')} ", font=("Malgun Gothic", 10, "bold"),
                bg=SlateTheme.BG_CARD_HOVER, fg=SlateTheme.TEXT_MUTED, padx=6, pady=2
            )
            lbl_badge.pack(side=tk.LEFT)

            lbl_status = tk.Label(
                top_row, text=f" 새로운 약정 목표를 설정하고 시작하세요.",
                font=("Malgun Gothic", 9.5), bg=SlateTheme.BG_CARD_LIGHT, fg=SlateTheme.TEXT_MUTED
            )
            lbl_status.pack(side=tk.LEFT, padx=8)

        # 오늘 사용량 표시
        s_sec = self.config.get("daily_solo_played_seconds", 0)
        p_sec = self.config.get("daily_party_played_seconds", 0)
        s_text = f"{s_sec // 60}분"
        p_text = f"{p_sec // 60}분"

        lbl_usage = tk.Label(
            banner, text=t("dash_today_usage", solo_used=s_text, party_used=p_text),
            font=("Malgun Gothic", 9), bg=SlateTheme.BG_CARD_LIGHT, fg=SlateTheme.ACCENT_CYAN
        )
        lbl_usage.pack(anchor="w", pady=(4, 0))

    def _sync_combobox(self, cb: ttk.Combobox, target_minutes: int):
        for disp, mins in self.TIME_OPTIONS:
            if mins == target_minutes:
                cb.set(disp)
                return
        cb.set(self.TIME_OPTIONS[1][0])

    def _on_time_selected(self, cb: ttk.Combobox, target_var: tk.IntVar):
        sel = cb.get()
        for disp, mins in self.TIME_OPTIONS:
            if disp == sel:
                target_var.set(mins)
                break

    def _on_solo_rule_change(self):
        if self.var_solo_rule.get() == "time_limit":
            self.cb_solo_time.config(state="readonly")
        else:
            self.cb_solo_time.config(state="disabled")

    def _on_party_rule_change(self):
        if self.var_party_rule.get() == "time_limit":
            self.cb_party_time.config(state="readonly")
        else:
            self.cb_party_time.config(state="disabled")

    def _on_language_changed(self, event=None):
        new_lang = self.var_lang.get()
        set_language(new_lang)
        self._build_ui()

    def _on_otp_toggle(self):
        if self.var_otp_enabled.get() and not self.otp_secret:
            self.open_otp_setup()

    def open_otp_setup(self):
        OTPSetupDialog(self, self.otp_secret, on_complete=self._on_secret_configured)

    def _on_secret_configured(self, new_secret: str):
        self.otp_secret = new_secret
        self.var_otp_enabled.set(True)

    def check_update_manual(self):
        def _check():
            has_update, tag, body, url = get_latest_version_info()
            if has_update:
                if messagebox.askyesno(
                    t("update_found_title"),
                    t("update_found_msg", tag=tag),
                    parent=self
                ):
                    open_release_page(url)
            else:
                messagebox.showinfo(t("update_latest_title"), t("update_latest_msg", version=CURRENT_VERSION), parent=self)
        threading.Thread(target=_check, daemon=True).start()

    def request_save(self):
        """저장 요청 시, 약정 잠금 중이거나 OTP가 활성화되어 있으면 마스터키/OTP 검증 필수"""
        is_locked = is_commitment_locked(self.config)
        has_otp = self.config.get("otp_enabled", False) and self.config.get("otp_secret")

        if is_locked or has_otp:
            OTPAuthDialog(self, self.config.get("otp_secret", ""), on_success=self._do_save)
        else:
            self._do_save()

    def _do_save(self):
        plan = self.var_commitment.get()
        end_date = calculate_commitment_end_date(plan)

        new_config = {
            "language": self.var_lang.get(),
            "commitment_plan": plan,
            "commitment_end_date": end_date,
            "solo_rule": self.var_solo_rule.get(),
            "solo_limit_minutes": int(self.var_solo_limit.get()),
            "party_rule": self.var_party_rule.get(),
            "party_limit_minutes": int(self.var_party_limit.get()),
            "night_lock": self.var_night_lock.get(),
            "night_start": self.var_night_start.get(),
            "night_end": self.var_night_end.get(),
            "otp_enabled": self.var_otp_enabled.get(),
            "otp_secret": self.otp_secret,
            "auto_start": self.var_auto_start.get(),
            "riot_id": self.var_riot_id.get().strip(),
            "riot_api_key": self.var_riot_key.get().strip(),
            "telemetry_enabled": self.var_telemetry.get(),
            "auto_update_check": self.var_auto_update.get(),
            "telemetry_uuid": self.config.get("telemetry_uuid", ""),
            "daily_played_date": self.config.get("daily_played_date"),
            "daily_solo_played_seconds": self.config.get("daily_solo_played_seconds", 0),
            "daily_party_played_seconds": self.config.get("daily_party_played_seconds", 0),
        }

        save_config(new_config)
        set_auto_start(new_config["auto_start"])
        self.config = new_config

        if self.on_config_updated:
            self.on_config_updated(new_config)

        messagebox.showinfo(t("save_success_title"), t("save_success_msg"), parent=self)
        self._build_ui()


def show_settings(on_config_updated=None):
    app = SettingsWindow(on_config_updated=on_config_updated)
    app.mainloop()


if __name__ == "__main__":
    show_settings()
