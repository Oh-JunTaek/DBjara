"""
DBjara - Tkinter GUI 설정 화면 및 OTP 다이얼로그 모듈
i18n 다국어 지원 (한국어 / English) 및 직관적인 다크 테마 UI를 제공합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional, Callable
from config import load_config, save_config, set_auto_start
from totp import generate_secret, verify_totp, get_otpauth_uri
from updater import get_latest_version_info, open_release_page, CURRENT_VERSION
from i18n import t, set_language, get_current_language

try:
    import qrcode
    from PIL import Image, ImageTk
    HAS_QR = True
except ImportError:
    HAS_QR = False


class DarkTheme:
    BG_DARK = "#121418"
    BG_CARD = "#1a1e24"
    BG_CARD_LIGHT = "#242a33"
    ACCENT_PRIMARY = "#3b82f6"
    ACCENT_HOVER = "#2563eb"
    ACCENT_SUCCESS = "#10b981"
    ACCENT_DANGER = "#ef4444"
    TEXT_MAIN = "#f3f4f6"
    TEXT_MUTED = "#9ca3af"
    BORDER = "#2e3744"


class OTPAuthDialog(tk.Toplevel):
    """동반자의 스마트폰에 표시된 6자리 OTP 입력을 요구하는 모달 창입니다."""

    def __init__(self, parent, secret: str, on_success: Callable[[], None]):
        super().__init__(parent)
        self.secret = secret
        self.on_success = on_success
        self.title(t("otp_auth_title"))
        self.geometry("380x260")
        self.resizable(False, False)
        self.configure(bg=DarkTheme.BG_DARK)
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
        pad = tk.Frame(self, bg=DarkTheme.BG_DARK, padx=24, pady=20)
        pad.pack(fill=tk.BOTH, expand=True)

        lbl_title = tk.Label(
            pad, text=t("otp_auth_title"), font=("Malgun Gothic", 13, "bold"),
            bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MAIN
        )
        lbl_title.pack(pady=(0, 4))

        lbl_desc = tk.Label(
            pad, text=t("otp_auth_desc"), font=("Malgun Gothic", 9),
            bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MUTED, justify=tk.CENTER
        )
        lbl_desc.pack(pady=6)

        self.entry_otp = tk.Entry(
            pad, font=("Consolas", 18, "bold"), justify=tk.CENTER,
            bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.TEXT_MAIN,
            insertbackground=DarkTheme.TEXT_MAIN, bd=0, highlightthickness=1,
            highlightcolor=DarkTheme.ACCENT_PRIMARY, highlightbackground=DarkTheme.BORDER
        )
        self.entry_otp.pack(ipady=4, fill=tk.X, pady=6)
        self.entry_otp.focus_set()
        self.entry_otp.bind("<Return>", lambda e: self.verify())

        self.lbl_error = tk.Label(
            pad, text="", font=("Malgun Gothic", 9), bg=DarkTheme.BG_DARK, fg=DarkTheme.ACCENT_DANGER
        )
        self.lbl_error.pack(pady=(0, 6))

        btn_frame = tk.Frame(pad, bg=DarkTheme.BG_DARK)
        btn_frame.pack(fill=tk.X)

        btn_submit = tk.Button(
            btn_frame, text=t("otp_auth_btn"), font=("Malgun Gothic", 10, "bold"),
            bg=DarkTheme.ACCENT_PRIMARY, fg="white", activebackground=DarkTheme.ACCENT_HOVER,
            activeforeground="white", bd=0, relief=tk.FLAT, pady=6, cursor="hand2",
            command=self.verify
        )
        btn_submit.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        btn_cancel = tk.Button(
            btn_frame, text=t("otp_cancel_btn"), font=("Malgun Gothic", 10),
            bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.TEXT_MUTED, bd=0, relief=tk.FLAT,
            pady=6, cursor="hand2", command=self.destroy
        )
        btn_cancel.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(4, 0))

    def verify(self):
        code = self.entry_otp.get().strip()
        if verify_totp(self.secret, code):
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
        self.geometry("450x580")
        self.resizable(False, False)
        self.configure(bg=DarkTheme.BG_DARK)
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
        pad = tk.Frame(self, bg=DarkTheme.BG_DARK, padx=24, pady=20)
        pad.pack(fill=tk.BOTH, expand=True)

        lbl_title = tk.Label(
            pad, text=t("otp_setup_head"), font=("Malgun Gothic", 13, "bold"),
            bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MAIN
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            pad, text=t("otp_setup_sub"), font=("Malgun Gothic", 9),
            bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MUTED, justify=tk.LEFT
        )
        lbl_sub.pack(anchor="w", pady=(4, 12))

        # QR 코드 표시 영역
        qr_frame = tk.Frame(pad, bg=DarkTheme.BG_CARD, bd=1, relief=tk.FLAT, padx=10, pady=10)
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
                qr_frame, text="[QR Error] Secret Key Only",
                bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MUTED, font=("Malgun Gothic", 9), pady=30, padx=20
            )
            lbl_no_qr.pack()

        # 비밀키 표시 및 복사 버튼
        key_box = tk.Frame(pad, bg=DarkTheme.BG_CARD_LIGHT, padx=10, pady=6)
        key_box.pack(fill=tk.X, pady=12)

        lbl_key_title = tk.Label(key_box, text=t("otp_key_title"), font=("Malgun Gothic", 8), bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.TEXT_MUTED)
        lbl_key_title.pack(anchor="w")

        key_row = tk.Frame(key_box, bg=DarkTheme.BG_CARD_LIGHT)
        key_row.pack(fill=tk.X, pady=2)

        self.lbl_secret = tk.Label(
            key_row, text=self.secret, font=("Consolas", 12, "bold"),
            bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.ACCENT_PRIMARY
        )
        self.lbl_secret.pack(side=tk.LEFT)

        btn_copy = tk.Button(
            key_row, text=t("otp_copy_btn"), font=("Malgun Gothic", 8),
            bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN, bd=0, padx=8, pady=2,
            cursor="hand2", command=self.copy_key
        )
        btn_copy.pack(side=tk.RIGHT)

        # 등록 검증 테스트 필드
        lbl_test = tk.Label(
            pad, text=t("otp_test_label"),
            font=("Malgun Gothic", 9), bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MAIN
        )
        lbl_test.pack(anchor="w", pady=(6, 2))

        test_row = tk.Frame(pad, bg=DarkTheme.BG_DARK)
        test_row.pack(fill=tk.X, pady=2)

        self.entry_test = tk.Entry(
            test_row, font=("Consolas", 12), justify=tk.CENTER,
            bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.TEXT_MAIN,
            insertbackground=DarkTheme.TEXT_MAIN, bd=0, highlightthickness=1,
            highlightcolor=DarkTheme.ACCENT_PRIMARY, highlightbackground=DarkTheme.BORDER, width=10
        )
        self.entry_test.pack(side=tk.LEFT, ipady=3)

        btn_test = tk.Button(
            test_row, text=t("otp_test_btn"), font=("Malgun Gothic", 9, "bold"),
            bg=DarkTheme.ACCENT_PRIMARY, fg="white", bd=0, padx=12, pady=4,
            cursor="hand2", command=self.test_and_save
        )
        btn_test.pack(side=tk.LEFT, padx=8)

        self.lbl_msg = tk.Label(pad, text="", font=("Malgun Gothic", 9), bg=DarkTheme.BG_DARK)
        self.lbl_msg.pack(pady=4)

    def copy_key(self):
        self.clipboard_clear()
        self.clipboard_append(self.secret)
        messagebox.showinfo(t("copied_title"), t("copied_msg"), parent=self)

    def test_and_save(self):
        code = self.entry_test.get().strip()
        if not code:
            self.lbl_msg.config(text=t("otp_test_empty"), fg=DarkTheme.ACCENT_DANGER)
            return

        if verify_totp(self.secret, code):
            messagebox.showinfo(t("save_success_title"), t("otp_test_success"), parent=self)
            self.destroy()
            self.on_complete(self.secret)
        else:
            self.lbl_msg.config(text=t("otp_err_mismatch"), fg=DarkTheme.ACCENT_DANGER)


class SettingsWindow(tk.Tk):
    """DBjara 메인 설정 창 클래스입니다."""

    def __init__(self, on_config_updated: Optional[Callable[[dict], None]] = None):
        super().__init__()
        self.on_config_updated = on_config_updated
        self.config = load_config()

        self.title(t("app_title"))
        self.geometry("560x820")
        self.resizable(False, False)
        self.configure(bg=DarkTheme.BG_DARK)

        self._init_variables()
        self.main_frame = None
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
        self.var_mode = tk.StringVar(value=self.config.get("mode", "medium"))
        self.var_daily_limit = tk.IntVar(value=self.config.get("daily_limit_minutes", 120))
        self.var_night_lock = tk.BooleanVar(value=self.config.get("night_lock", True))
        self.var_night_start = tk.StringVar(value=self.config.get("night_start", "23:00"))
        self.var_night_end = tk.StringVar(value=self.config.get("night_end", "07:00"))
        self.var_otp_enabled = tk.BooleanVar(value=self.config.get("otp_enabled", False))
        self.var_auto_start = tk.BooleanVar(value=self.config.get("auto_start", False))
        self.var_riot_id = tk.StringVar(value=self.config.get("riot_id", ""))
        self.var_riot_key = tk.StringVar(value=self.config.get("riot_api_key", ""))
        self.var_telemetry = tk.BooleanVar(value=self.config.get("telemetry_enabled", True))
        self.var_auto_update = tk.BooleanVar(value=self.config.get("auto_update_check", True))
        self.otp_secret = self.config.get("otp_secret", "")

    def _build_ui(self):
        if self.main_frame:
            self.main_frame.destroy()

        self.title(t("app_title"))
        self.main_frame = tk.Frame(self, bg=DarkTheme.BG_DARK, padx=20, pady=16)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 상단 헤더
        head = tk.Frame(self.main_frame, bg=DarkTheme.BG_DARK)
        head.pack(fill=tk.X, pady=(0, 10))

        title_row = tk.Frame(head, bg=DarkTheme.BG_DARK)
        title_row.pack(fill=tk.X)

        title = tk.Label(
            title_row, text=t("app_name"), font=("Malgun Gothic", 15, "bold"),
            bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MAIN
        )
        title.pack(side=tk.LEFT)

        lbl_ver = tk.Label(
            title_row, text=f"{CURRENT_VERSION}", font=("Consolas", 9, "bold"),
            bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.ACCENT_PRIMARY, padx=6, pady=2
        )
        lbl_ver.pack(side=tk.LEFT, padx=8)

        # 언어 선택 콤보박스
        lang_frame = tk.Frame(title_row, bg=DarkTheme.BG_DARK)
        lang_frame.pack(side=tk.RIGHT)

        lbl_l = tk.Label(lang_frame, text="🌐", font=("Segoe UI Emoji", 10), bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MUTED)
        lbl_l.pack(side=tk.LEFT, padx=(0, 4))

        cb_lang = ttk.Combobox(
            lang_frame, textvariable=self.var_lang, values=["ko", "en"],
            state="readonly", width=5
        )
        cb_lang.pack(side=tk.LEFT)
        cb_lang.bind("<<ComboboxSelected>>", self._on_language_changed)

        btn_update = tk.Button(
            title_row, text=t("btn_update_check"), font=("Malgun Gothic", 8),
            bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.TEXT_MAIN, bd=0, padx=6, pady=2,
            cursor="hand2", command=self.check_update_manual
        )
        btn_update.pack(side=tk.RIGHT, padx=6)

        sub = tk.Label(
            head, text=t("app_sub"), font=("Malgun Gothic", 8),
            bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MUTED
        )
        sub.pack(anchor="w", pady=(2, 0))

        # 섹션 1: 통제 강도 설정
        card1 = tk.LabelFrame(
            self.main_frame, text=t("sec_mode"), font=("Malgun Gothic", 9, "bold"),
            bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN, bd=1, relief=tk.SOLID, padx=12, pady=6
        )
        card1.pack(fill=tk.X, pady=(0, 8))

        r_high = tk.Radiobutton(
            card1, text=t("mode_high"), variable=self.var_mode, value="high",
            font=("Malgun Gothic", 9, "bold"), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN,
            selectcolor=DarkTheme.BG_CARD_LIGHT, activebackground=DarkTheme.BG_CARD,
            activeforeground=DarkTheme.TEXT_MAIN, command=self._on_mode_change
        )
        r_high.pack(anchor="w")

        r_med = tk.Radiobutton(
            card1, text=t("mode_medium"), variable=self.var_mode, value="medium",
            font=("Malgun Gothic", 9, "bold"), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN,
            selectcolor=DarkTheme.BG_CARD_LIGHT, activebackground=DarkTheme.BG_CARD,
            activeforeground=DarkTheme.TEXT_MAIN, command=self._on_mode_change
        )
        r_med.pack(anchor="w")

        r_low = tk.Radiobutton(
            card1, text=t("mode_low"), variable=self.var_mode, value="low",
            font=("Malgun Gothic", 9, "bold"), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN,
            selectcolor=DarkTheme.BG_CARD_LIGHT, activebackground=DarkTheme.BG_CARD,
            activeforeground=DarkTheme.TEXT_MAIN, command=self._on_mode_change
        )
        r_low.pack(anchor="w")

        self.frame_low_opts = tk.Frame(card1, bg=DarkTheme.BG_CARD)
        self.frame_low_opts.pack(fill=tk.X, padx=16, pady=(2, 4))
        self.lbl_limit = tk.Label(
            self.frame_low_opts, text=t("daily_limit_label", minutes=self.var_daily_limit.get()),
            font=("Malgun Gothic", 8), bg=DarkTheme.BG_CARD, fg=DarkTheme.ACCENT_PRIMARY
        )
        self.lbl_limit.pack(anchor="w")
        self.scale_limit = ttk.Scale(self.frame_low_opts, from_=30, to=240, variable=self.var_daily_limit, command=self._on_slider_change)
        self.scale_limit.pack(fill=tk.X)
        self._on_mode_change()

        # 섹션 2: 야간 시간 통제
        card2 = tk.LabelFrame(
            self.main_frame, text=t("sec_night"), font=("Malgun Gothic", 9, "bold"),
            bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN, bd=1, relief=tk.SOLID, padx=12, pady=6
        )
        card2.pack(fill=tk.X, pady=(0, 8))

        chk_night = tk.Checkbutton(
            card2, text=t("night_lock_chk"), variable=self.var_night_lock,
            font=("Malgun Gothic", 9, "bold"), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN,
            selectcolor=DarkTheme.BG_CARD_LIGHT, activebackground=DarkTheme.BG_CARD,
            activeforeground=DarkTheme.TEXT_MAIN
        )
        chk_night.pack(anchor="w")

        time_row = tk.Frame(card2, bg=DarkTheme.BG_CARD)
        time_row.pack(fill=tk.X, pady=(4, 0), padx=16)
        lbl_t1 = tk.Label(time_row, text=t("night_start"), font=("Malgun Gothic", 8), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MUTED)
        lbl_t1.pack(side=tk.LEFT)
        entry_n_start = tk.Entry(time_row, textvariable=self.var_night_start, width=6, justify=tk.CENTER, bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.TEXT_MAIN, bd=0)
        entry_n_start.pack(side=tk.LEFT, padx=4)
        lbl_t2 = tk.Label(time_row, text=t("night_end"), font=("Malgun Gothic", 8), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MUTED)
        lbl_t2.pack(side=tk.LEFT, padx=(10, 0))
        entry_n_end = tk.Entry(time_row, textvariable=self.var_night_end, width=6, justify=tk.CENTER, bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.TEXT_MAIN, bd=0)
        entry_n_end.pack(side=tk.LEFT, padx=4)

        # 섹션 3: 동반자 OTP & 부팅 설정
        card3 = tk.LabelFrame(
            self.main_frame, text=t("sec_lock"), font=("Malgun Gothic", 9, "bold"),
            bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN, bd=1, relief=tk.SOLID, padx=12, pady=6
        )
        card3.pack(fill=tk.X, pady=(0, 8))

        chk_otp = tk.Checkbutton(
            card3, text=t("otp_chk"), variable=self.var_otp_enabled,
            font=("Malgun Gothic", 9), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN,
            selectcolor=DarkTheme.BG_CARD_LIGHT, activebackground=DarkTheme.BG_CARD,
            activeforeground=DarkTheme.TEXT_MAIN, command=self._on_otp_toggle
        )
        chk_otp.pack(anchor="w")

        self.btn_otp_setup = tk.Button(
            card3, text=t("otp_view_btn"), font=("Malgun Gothic", 8),
            bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.TEXT_MAIN, bd=0, padx=8, pady=3,
            cursor="hand2", command=self.open_otp_setup
        )
        self.btn_otp_setup.pack(anchor="w", padx=16, pady=(3, 4))

        chk_auto = tk.Checkbutton(
            card3, text=t("auto_start_chk"), variable=self.var_auto_start,
            font=("Malgun Gothic", 9), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN,
            selectcolor=DarkTheme.BG_CARD_LIGHT, activebackground=DarkTheme.BG_CARD,
            activeforeground=DarkTheme.TEXT_MAIN
        )
        chk_auto.pack(anchor="w")

        # 섹션 4: Riot ID 전적 검증
        card4 = tk.LabelFrame(
            self.main_frame, text=t("sec_riot"), font=("Malgun Gothic", 9, "bold"),
            bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN, bd=1, relief=tk.SOLID, padx=12, pady=6
        )
        card4.pack(fill=tk.X, pady=(0, 8))

        lbl_riot_desc = tk.Label(
            card4, text=t("riot_desc"), font=("Malgun Gothic", 8),
            bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MUTED
        )
        lbl_riot_desc.pack(anchor="w")

        riot_row = tk.Frame(card4, bg=DarkTheme.BG_CARD)
        riot_row.pack(fill=tk.X, pady=(4, 2))

        lbl_rid = tk.Label(riot_row, text=t("riot_id_label"), font=("Malgun Gothic", 8), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN)
        lbl_rid.pack(side=tk.LEFT)

        entry_rid = tk.Entry(
            riot_row, textvariable=self.var_riot_id, width=22,
            bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.TEXT_MAIN, bd=0
        )
        entry_rid.pack(side=tk.LEFT, padx=6)

        # 섹션 5: 통계 및 자동 업데이트 설정
        card5 = tk.LabelFrame(
            self.main_frame, text=t("sec_meta"), font=("Malgun Gothic", 9, "bold"),
            bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN, bd=1, relief=tk.SOLID, padx=12, pady=6
        )
        card5.pack(fill=tk.X, pady=(0, 10))

        chk_telem = tk.Checkbutton(
            card5, text=t("telemetry_chk"), variable=self.var_telemetry,
            font=("Malgun Gothic", 8), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN,
            selectcolor=DarkTheme.BG_CARD_LIGHT, activebackground=DarkTheme.BG_CARD,
            activeforeground=DarkTheme.TEXT_MAIN
        )
        chk_telem.pack(anchor="w")

        chk_au = tk.Checkbutton(
            card5, text=t("auto_update_chk"), variable=self.var_auto_update,
            font=("Malgun Gothic", 8), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN,
            selectcolor=DarkTheme.BG_CARD_LIGHT, activebackground=DarkTheme.BG_CARD,
            activeforeground=DarkTheme.TEXT_MAIN
        )
        chk_au.pack(anchor="w")

        # 저장 버튼
        btn_save = tk.Button(
            self.main_frame, text=t("btn_save"), font=("Malgun Gothic", 10, "bold"),
            bg=DarkTheme.ACCENT_PRIMARY, fg="white", activebackground=DarkTheme.ACCENT_HOVER,
            activeforeground="white", bd=0, relief=tk.FLAT, pady=6, cursor="hand2",
            command=self.request_save
        )
        btn_save.pack(fill=tk.X)

    def _on_language_changed(self, event=None):
        new_lang = self.var_lang.get()
        set_language(new_lang)
        self._build_ui()

    def _on_mode_change(self):
        if self.var_mode.get() == "low":
            self.frame_low_opts.pack(fill=tk.X, padx=16, pady=(2, 4))
        else:
            self.frame_low_opts.pack_forget()

    def _on_slider_change(self, val):
        self.lbl_limit.config(text=t("daily_limit_label", minutes=int(float(val))))

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
        if self.config.get("otp_enabled", False) and self.config.get("otp_secret"):
            OTPAuthDialog(self, self.config.get("otp_secret"), on_success=self._do_save)
        else:
            self._do_save()

    def _do_save(self):
        new_config = {
            "language": self.var_lang.get(),
            "mode": self.var_mode.get(),
            "daily_limit_minutes": int(self.var_daily_limit.get()),
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
            "daily_played_seconds": self.config.get("daily_played_seconds", 0),
        }

        save_config(new_config)
        set_auto_start(new_config["auto_start"])
        self.config = new_config

        if self.on_config_updated:
            self.on_config_updated(new_config)

        messagebox.showinfo(t("save_success_title"), t("save_success_msg"), parent=self)
        self.destroy()


def show_settings(on_config_updated=None):
    app = SettingsWindow(on_config_updated=on_config_updated)
    app.mainloop()


if __name__ == "__main__":
    show_settings()
