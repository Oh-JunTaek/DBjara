"""
Modern Tkinter GUI for dbjara
Provides Settings Window, Companion OTP Management, and Verification Dialogs.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import io
from typing import Optional, Callable
from config import load_config, save_config, set_auto_start
from totp import generate_secret, verify_totp, get_otpauth_uri

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
    ACCENT_PRIMARY = "#3b82f6"  # Blue
    ACCENT_HOVER = "#2563eb"
    ACCENT_DANGER = "#ef4444"   # Red for night/hard block
    TEXT_MAIN = "#f3f4f6"
    TEXT_MUTED = "#9ca3af"
    BORDER = "#2e3744"


class OTPAuthDialog(tk.Toplevel):
    """Modal dialog prompting user to input 6-digit OTP from their companion."""

    def __init__(self, parent, secret: str, on_success: Callable[[], None]):
        super().__init__(parent)
        self.secret = secret
        self.on_success = on_success
        self.title("동반자 OTP 인증 - 디비자라")
        self.geometry("380x280")
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

        lbl_icon = tk.Label(
            pad, text="🔒", font=("Segoe UI Emoji", 32), bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MAIN
        )
        lbl_icon.pack(pady=(0, 5))

        lbl_title = tk.Label(
            pad, text="동반자 OTP 인증 필요", font=("Malgun Gothic", 13, "bold"),
            bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MAIN
        )
        lbl_title.pack()

        lbl_desc = tk.Label(
            pad,
            text="설정 변경 또는 앱 종료를 위해\n동반자(친구)의 스마트폰 OTP 번호 6자리를 입력하세요.",
            font=("Malgun Gothic", 9), bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MUTED, justify=tk.CENTER
        )
        lbl_desc.pack(pady=8)

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
            btn_frame, text="인증하기", font=("Malgun Gothic", 10, "bold"),
            bg=DarkTheme.ACCENT_PRIMARY, fg="white", activebackground=DarkTheme.ACCENT_HOVER,
            activeforeground="white", bd=0, relief=tk.FLAT, pady=6, cursor="hand2",
            command=self.verify
        )
        btn_submit.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        btn_cancel = tk.Button(
            btn_frame, text="취소", font=("Malgun Gothic", 10),
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
            self.lbl_error.config(text="번호가 일치하지 않습니다. 다시 확인하세요.")
            self.entry_otp.delete(0, tk.END)


class OTPSetupDialog(tk.Toplevel):
    """Setup dialog to show secret key & QR code to register in companion's phone."""

    def __init__(self, parent, current_secret: str, on_complete: Callable[[str], None]):
        super().__init__(parent)
        self.secret = current_secret if current_secret else generate_secret()
        self.on_complete = on_complete
        self.title("동반자 등록 (Google Authenticator) - 디비자라")
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
            pad, text="동반자(친구/가족) 스마트폰 등록", font=("Malgun Gothic", 13, "bold"),
            bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MAIN
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            pad,
            text="친구의 스마트폰(Google Authenticator 앱 등)으로\n아래 QR 코드를 스캔하거나 비밀키를 직접 입력해 등록하세요.",
            font=("Malgun Gothic", 9), bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MUTED, justify=tk.LEFT
        )
        lbl_sub.pack(anchor="w", pady=(4, 12))

        # QR Code Container
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
                qr_frame, text="[QR 모듈 미설치]\n아래 시크릿 키를 직접 입력하세요.",
                bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MUTED, font=("Malgun Gothic", 9), pady=30, padx=20
            )
            lbl_no_qr.pack()

        # Secret Key display & copy
        key_box = tk.Frame(pad, bg=DarkTheme.BG_CARD_LIGHT, padx=10, pady=6)
        key_box.pack(fill=tk.X, pady=12)

        lbl_key_title = tk.Label(key_box, text="등록용 비밀키(Secret Key):", font=("Malgun Gothic", 8), bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.TEXT_MUTED)
        lbl_key_title.pack(anchor="w")

        key_row = tk.Frame(key_box, bg=DarkTheme.BG_CARD_LIGHT)
        key_row.pack(fill=tk.X, pady=2)

        self.lbl_secret = tk.Label(
            key_row, text=self.secret, font=("Consolas", 12, "bold"),
            bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.ACCENT_PRIMARY
        )
        self.lbl_secret.pack(side=tk.LEFT)

        btn_copy = tk.Button(
            key_row, text="복사", font=("Malgun Gothic", 8),
            bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN, bd=0, padx=8, pady=2,
            cursor="hand2", command=self.copy_key
        )
        btn_copy.pack(side=tk.RIGHT)

        # Verification Test
        lbl_test = tk.Label(
            pad, text="등록 후 친구의 폰에 생성된 6자리 번호로 테스트:",
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
            test_row, text="테스트 및 등록 완료", font=("Malgun Gothic", 9, "bold"),
            bg=DarkTheme.ACCENT_PRIMARY, fg="white", bd=0, padx=12, pady=4,
            cursor="hand2", command=self.test_and_save
        )
        btn_test.pack(side=tk.LEFT, padx=8)

        self.lbl_msg = tk.Label(pad, text="", font=("Malgun Gothic", 9), bg=DarkTheme.BG_DARK)
        self.lbl_msg.pack(pady=4)

    def copy_key(self):
        self.clipboard_clear()
        self.clipboard_append(self.secret)
        messagebox.showinfo("복사 완료", "비밀키가 클립보드에 복사되었습니다.", parent=self)

    def test_and_save(self):
        code = self.entry_test.get().strip()
        if not code:
            self.lbl_msg.config(text="6자리 번호를 입력해주세요.", fg=DarkTheme.ACCENT_DANGER)
            return

        if verify_totp(self.secret, code):
            messagebox.showinfo("성공", "동반자 OTP가 정상적으로 등록 및 검증되었습니다!", parent=self)
            self.destroy()
            self.on_complete(self.secret)
        else:
            self.lbl_msg.config(text="번호가 일치하지 않습니다. 다시 확인하세요.", fg=DarkTheme.ACCENT_DANGER)


class SettingsWindow(tk.Tk):
    """Main Settings Window for dbjara."""

    def __init__(self, on_config_updated: Optional[Callable[[dict], None]] = None):
        super().__init__()
        self.on_config_updated = on_config_updated
        self.config = load_config()

        self.title("디비자라 (dbjara) - LoL 솔로 랭크 통제기")
        self.geometry("520x680")
        self.resizable(False, False)
        self.configure(bg=DarkTheme.BG_DARK)

        self._init_variables()
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
        self.var_mode = tk.StringVar(value=self.config.get("mode", "medium"))
        self.var_daily_limit = tk.IntVar(value=self.config.get("daily_limit_minutes", 120))
        self.var_night_lock = tk.BooleanVar(value=self.config.get("night_lock", True))
        self.var_night_start = tk.StringVar(value=self.config.get("night_start", "23:00"))
        self.var_night_end = tk.StringVar(value=self.config.get("night_end", "07:00"))
        self.var_otp_enabled = tk.BooleanVar(value=self.config.get("otp_enabled", False))
        self.var_auto_start = tk.BooleanVar(value=self.config.get("auto_start", False))
        self.otp_secret = self.config.get("otp_secret", "")

    def _build_ui(self):
        main = tk.Frame(self, bg=DarkTheme.BG_DARK, padx=24, pady=20)
        main.pack(fill=tk.BOTH, expand=True)

        # Header
        head = tk.Frame(main, bg=DarkTheme.BG_DARK)
        head.pack(fill=tk.X, pady=(0, 16))

        title = tk.Label(
            head, text="🌙 디비자라 (dbjara)", font=("Malgun Gothic", 16, "bold"),
            bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MAIN
        )
        title.pack(anchor="w")

        sub = tk.Label(
            head, text="친구와의 게임은 즐겁게, 혼자만의 밤샘 솔랭은 강력하게 통제합니다.",
            font=("Malgun Gothic", 9), bg=DarkTheme.BG_DARK, fg=DarkTheme.TEXT_MUTED
        )
        sub.pack(anchor="w")

        # Section 1: 통제 강도 설정
        card1 = tk.LabelFrame(
            main, text=" 🛡️ 통제 강도 설정 ", font=("Malgun Gothic", 10, "bold"),
            bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN, bd=1, relief=tk.SOLID, padx=14, pady=10
        )
        card1.pack(fill=tk.X, pady=(0, 12))

        # Mode High
        r_high = tk.Radiobutton(
            card1, text="상 (High): 롤 실행 자체 차단", variable=self.var_mode, value="high",
            font=("Malgun Gothic", 9, "bold"), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN,
            selectcolor=DarkTheme.BG_CARD_LIGHT, activebackground=DarkTheme.BG_CARD,
            activeforeground=DarkTheme.TEXT_MAIN, command=self._on_mode_change
        )
        r_high.pack(anchor="w")
        lbl_h_desc = tk.Label(card1, text="  └ 롤 클라이언트 실행 즉시 프로세스를 강제 종료합니다.", font=("Malgun Gothic", 8), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MUTED)
        lbl_h_desc.pack(anchor="w", pady=(0, 6))

        # Mode Medium
        r_med = tk.Radiobutton(
            card1, text="중 (Medium): 솔로(1인) 플레이 금지 (권장 ⭐)", variable=self.var_mode, value="medium",
            font=("Malgun Gothic", 9, "bold"), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN,
            selectcolor=DarkTheme.BG_CARD_LIGHT, activebackground=DarkTheme.BG_CARD,
            activeforeground=DarkTheme.TEXT_MAIN, command=self._on_mode_change
        )
        r_med.pack(anchor="w")
        lbl_m_desc = tk.Label(card1, text="  └ 1인 큐 매칭 시 즉시 매칭 취소! (2인 이상 다인큐만 허용)", font=("Malgun Gothic", 8), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MUTED)
        lbl_m_desc.pack(anchor="w", pady=(0, 6))

        # Mode Low
        r_low = tk.Radiobutton(
            card1, text="하 (Low): 일일 솔로 시간 제한", variable=self.var_mode, value="low",
            font=("Malgun Gothic", 9, "bold"), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN,
            selectcolor=DarkTheme.BG_CARD_LIGHT, activebackground=DarkTheme.BG_CARD,
            activeforeground=DarkTheme.TEXT_MAIN, command=self._on_mode_change
        )
        r_low.pack(anchor="w")

        self.frame_low_opts = tk.Frame(card1, bg=DarkTheme.BG_CARD)
        self.frame_low_opts.pack(fill=tk.X, padx=16, pady=(2, 4))

        self.lbl_limit = tk.Label(self.frame_low_opts, text=f"하루 최대 솔로 시간: {self.var_daily_limit.get()}분", font=("Malgun Gothic", 8), bg=DarkTheme.BG_CARD, fg=DarkTheme.ACCENT_PRIMARY)
        self.lbl_limit.pack(anchor="w")

        self.scale_limit = ttk.Scale(
            self.frame_low_opts, from_=30, to=240, variable=self.var_daily_limit,
            command=self._on_slider_change
        )
        self.scale_limit.pack(fill=tk.X)

        self._on_mode_change()

        # Section 2: 야간 시간 통제
        card2 = tk.LabelFrame(
            main, text=" 🌙 야간 시간 강제 차단 (디비자라 모드) ", font=("Malgun Gothic", 10, "bold"),
            bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN, bd=1, relief=tk.SOLID, padx=14, pady=10
        )
        card2.pack(fill=tk.X, pady=(0, 12))

        chk_night = tk.Checkbutton(
            card2, text="야간 시간대 게임 완전 차단 (동반자 무관 강제 종료)", variable=self.var_night_lock,
            font=("Malgun Gothic", 9, "bold"), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN,
            selectcolor=DarkTheme.BG_CARD_LIGHT, activebackground=DarkTheme.BG_CARD,
            activeforeground=DarkTheme.TEXT_MAIN
        )
        chk_night.pack(anchor="w")

        time_row = tk.Frame(card2, bg=DarkTheme.BG_CARD)
        time_row.pack(fill=tk.X, pady=(6, 0), padx=16)

        lbl_t1 = tk.Label(time_row, text="차단 시작:", font=("Malgun Gothic", 9), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MUTED)
        lbl_t1.pack(side=tk.LEFT)
        entry_n_start = tk.Entry(time_row, textvariable=self.var_night_start, width=6, justify=tk.CENTER, bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.TEXT_MAIN, bd=0)
        entry_n_start.pack(side=tk.LEFT, padx=4)

        lbl_t2 = tk.Label(time_row, text="~ 종료:", font=("Malgun Gothic", 9), bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MUTED)
        lbl_t2.pack(side=tk.LEFT, padx=(10, 0))
        entry_n_end = tk.Entry(time_row, textvariable=self.var_night_end, width=6, justify=tk.CENTER, bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.TEXT_MAIN, bd=0)
        entry_n_end.pack(side=tk.LEFT, padx=4)

        # Section 3: 동반자 OTP & 부팅 설정
        card3 = tk.LabelFrame(
            main, text=" 🔒 자제력 자물쇠 (동반자 OTP & 자동 실행) ", font=("Malgun Gothic", 10, "bold"),
            bg=DarkTheme.BG_CARD, fg=DarkTheme.TEXT_MAIN, bd=1, relief=tk.SOLID, padx=14, pady=10
        )
        card3.pack(fill=tk.X, pady=(0, 16))

        chk_otp = tk.Checkbutton(
            card3, text="동반자 OTP 자물쇠 활성화 (설정 변경/앱 종료 시 OTP 요구)",
            variable=self.var_otp_enabled, font=("Malgun Gothic", 9), bg=DarkTheme.BG_CARD,
            fg=DarkTheme.TEXT_MAIN, selectcolor=DarkTheme.BG_CARD_LIGHT,
            activebackground=DarkTheme.BG_CARD, activeforeground=DarkTheme.TEXT_MAIN,
            command=self._on_otp_toggle
        )
        chk_otp.pack(anchor="w")

        self.btn_otp_setup = tk.Button(
            card3, text="📱 동반자 등록 QR / 비밀키 보기", font=("Malgun Gothic", 8),
            bg=DarkTheme.BG_CARD_LIGHT, fg=DarkTheme.TEXT_MAIN, bd=0, padx=8, pady=4,
            cursor="hand2", command=self.open_otp_setup
        )
        self.btn_otp_setup.pack(anchor="w", padx=16, pady=(4, 6))

        chk_auto = tk.Checkbutton(
            card3, text="윈도우 부팅 시 자동 실행 (백그라운드 상시 감시)",
            variable=self.var_auto_start, font=("Malgun Gothic", 9), bg=DarkTheme.BG_CARD,
            fg=DarkTheme.TEXT_MAIN, selectcolor=DarkTheme.BG_CARD_LIGHT,
            activebackground=DarkTheme.BG_CARD, activeforeground=DarkTheme.TEXT_MAIN
        )
        chk_auto.pack(anchor="w")

        # Save Button
        btn_save = tk.Button(
            main, text="설정 저장 및 적용", font=("Malgun Gothic", 11, "bold"),
            bg=DarkTheme.ACCENT_PRIMARY, fg="white", activebackground=DarkTheme.ACCENT_HOVER,
            activeforeground="white", bd=0, relief=tk.FLAT, pady=8, cursor="hand2",
            command=self.request_save
        )
        btn_save.pack(fill=tk.X)

    def _on_mode_change(self):
        if self.var_mode.get() == "low":
            self.frame_low_opts.pack(fill=tk.X, padx=16, pady=(2, 4))
        else:
            self.frame_low_opts.pack_forget()

    def _on_slider_change(self, val):
        self.lbl_limit.config(text=f"하루 최대 솔로 시간: {int(float(val))}분")

    def _on_otp_toggle(self):
        if self.var_otp_enabled.get() and not self.otp_secret:
            # Need to setup secret first
            self.open_otp_setup()

    def open_otp_setup(self):
        OTPSetupDialog(self, self.otp_secret, on_complete=self._on_secret_configured)

    def _on_secret_configured(self, new_secret: str):
        self.otp_secret = new_secret
        self.var_otp_enabled.set(True)

    def request_save(self):
        """Save settings, requiring OTP if it was previously enabled."""
        # If OTP was enabled in loaded config, user must verify before changing settings
        if self.config.get("otp_enabled", False) and self.config.get("otp_secret"):
            OTPAuthDialog(self, self.config.get("otp_secret"), on_success=self._do_save)
        else:
            self._do_save()

    def _do_save(self):
        new_config = {
            "mode": self.var_mode.get(),
            "daily_limit_minutes": int(self.var_daily_limit.get()),
            "night_lock": self.var_night_lock.get(),
            "night_start": self.var_night_start.get(),
            "night_end": self.var_night_end.get(),
            "otp_enabled": self.var_otp_enabled.get(),
            "otp_secret": self.otp_secret,
            "auto_start": self.var_auto_start.get(),
            "daily_played_date": self.config.get("daily_played_date"),
            "daily_played_seconds": self.config.get("daily_played_seconds", 0),
        }

        save_config(new_config)
        set_auto_start(new_config["auto_start"])
        self.config = new_config

        if self.on_config_updated:
            self.on_config_updated(new_config)

        messagebox.showinfo("저장 완료", "설정이 성공적으로 저장 및 적용되었습니다.", parent=self)
        self.destroy()


def show_settings(on_config_updated=None):
    app = SettingsWindow(on_config_updated=on_config_updated)
    app.mainloop()


if __name__ == "__main__":
    show_settings()
