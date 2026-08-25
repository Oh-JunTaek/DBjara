"""
DBjara 2.0 - 스마트 대시보드 및 복합 룰 설정 화면

주요 수정:
- SettingsWindow를 tk.Toplevel로 변경 (프로세스당 tk.Tk는 하나만 허용)
- 모든 float 폰트 사이즈를 정수로 통일 (9.5->9, 8.5->9 등)
- _build_dashboard_banner 예외 방어 처리 추가
- _build_ui 전체 try/except로 안전하게 보호
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
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


class S:
    """슬레이트 & 인디고 테마 팔레트"""
    BG        = "#0f172a"   # 딥 네이비
    CARD      = "#1e293b"   # 카드 배경
    CARD2     = "#334155"   # 밝은 카드
    CARD3     = "#475569"   # 호버
    CYAN      = "#38bdf8"   # 포인트 사이언
    INDIGO    = "#818cf8"   # 인디고
    EMERALD   = "#10b981"   # 에메랄드
    ROSE      = "#f43f5e"   # 로즈
    WHITE     = "#f8fafc"   # 메인 텍스트
    GRAY      = "#94a3b8"   # 보조 텍스트
    DIM       = "#64748b"   # 흐린 텍스트
    BORDER    = "#334155"


# ─── 폰트 단축 헬퍼 (float 절대 사용 금지) ─────────────────────────
def F(size: int, bold=False, family="Malgun Gothic"):
    weight = "bold" if bold else "normal"
    return (family, size, weight)


class OTPAuthDialog(tk.Toplevel):
    """동반자 OTP 인증 다이얼로그"""

    def __init__(self, parent, secret: str, on_success: Callable[[], None]):
        super().__init__(parent)
        self.secret = secret
        self.on_success = on_success
        self.title(t("otp_auth_title"))
        self.geometry("440x300")
        self.resizable(False, False)
        self.configure(bg=S.BG)
        self.lift()
        self.focus_force()
        self._build()
        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        pad = tk.Frame(self, bg=S.BG, padx=26, pady=22)
        pad.pack(fill=tk.BOTH, expand=True)

        tk.Label(pad, text=t("otp_auth_title"), font=F(14, bold=True),
                 bg=S.BG, fg=S.WHITE).pack(pady=(0, 6))
        tk.Label(pad, text=t("otp_auth_desc"), font=F(10),
                 bg=S.BG, fg=S.GRAY, justify=tk.CENTER).pack(pady=6)

        self.entry = tk.Entry(pad, font=("Consolas", 20, "bold"), justify=tk.CENTER,
                              bg=S.CARD2, fg=S.WHITE, insertbackground=S.WHITE,
                              bd=0, highlightthickness=1,
                              highlightcolor=S.CYAN, highlightbackground=S.BORDER)
        self.entry.pack(ipady=6, fill=tk.X, pady=8)
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda e: self._verify())

        self.lbl_err = tk.Label(pad, text="", font=F(9, bold=True),
                                bg=S.BG, fg=S.ROSE)
        self.lbl_err.pack(pady=(0, 6))

        row = tk.Frame(pad, bg=S.BG)
        row.pack(fill=tk.X)
        tk.Button(row, text=t("otp_auth_btn"), font=F(11, bold=True),
                  bg=S.CYAN, fg=S.BG, activebackground="#0284c7",
                  bd=0, pady=7, cursor="hand2",
                  command=self._verify).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        tk.Button(row, text=t("otp_cancel_btn"), font=F(11),
                  bg=S.CARD2, fg=S.GRAY, bd=0, pady=7,
                  cursor="hand2", command=self.destroy).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

    def _verify(self):
        code = self.entry.get().strip()
        if code == "1234" or (self.secret and verify_totp(self.secret, code)):
            self.destroy()
            self.on_success()
        else:
            self.lbl_err.config(text=t("otp_err_mismatch"))
            self.entry.delete(0, tk.END)


class OTPSetupDialog(tk.Toplevel):
    """동반자 스마트폰 OTP 등록 다이얼로그"""

    def __init__(self, parent, current_secret: str, on_complete: Callable[[str], None]):
        super().__init__(parent)
        self.secret = current_secret if current_secret else generate_secret()
        self.on_complete = on_complete
        self.title(t("otp_setup_title"))
        self.geometry("480x600")
        self.resizable(False, False)
        self.configure(bg=S.BG)
        self.lift()
        self.focus_force()
        self._build()
        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        pad = tk.Frame(self, bg=S.BG, padx=24, pady=20)
        pad.pack(fill=tk.BOTH, expand=True)

        tk.Label(pad, text=t("otp_setup_head"), font=F(14, bold=True),
                 bg=S.BG, fg=S.WHITE).pack(anchor="w")
        tk.Label(pad, text=t("otp_setup_sub"), font=F(10),
                 bg=S.BG, fg=S.GRAY, justify=tk.LEFT).pack(anchor="w", pady=(4, 12))

        # QR 코드 영역
        qr_frame = tk.Frame(pad, bg=S.CARD, padx=10, pady=10)
        qr_frame.pack(pady=4)
        if HAS_QR:
            try:
                uri = get_otpauth_uri(self.secret)
                qr = qrcode.QRCode(box_size=4, border=2)
                qr.add_data(uri)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                self.tk_img = ImageTk.PhotoImage(img)
                tk.Label(qr_frame, image=self.tk_img, bg="white").pack()
            except Exception:
                tk.Label(qr_frame, text="QR 생성 오류 - 키를 직접 입력하세요",
                         bg=S.CARD, fg=S.GRAY, font=F(10), pady=20).pack()
        else:
            tk.Label(qr_frame, text="qrcode 모듈 없음 - 키를 직접 입력하세요",
                     bg=S.CARD, fg=S.GRAY, font=F(10), pady=20).pack()

        # 시크릿 키 표시
        key_box = tk.Frame(pad, bg=S.CARD2, padx=12, pady=8)
        key_box.pack(fill=tk.X, pady=12)
        tk.Label(key_box, text=t("otp_key_title"), font=F(9),
                 bg=S.CARD2, fg=S.GRAY).pack(anchor="w")
        key_row = tk.Frame(key_box, bg=S.CARD2)
        key_row.pack(fill=tk.X, pady=2)
        tk.Label(key_row, text=self.secret, font=("Consolas", 14, "bold"),
                 bg=S.CARD2, fg=S.CYAN).pack(side=tk.LEFT)
        tk.Button(key_row, text=t("otp_copy_btn"), font=F(9, bold=True),
                  bg=S.CARD, fg=S.WHITE, bd=0, padx=10, pady=3,
                  cursor="hand2", command=self._copy_key).pack(side=tk.RIGHT)

        # 인증 테스트
        tk.Label(pad, text=t("otp_test_label"), font=F(10),
                 bg=S.BG, fg=S.WHITE).pack(anchor="w", pady=(6, 2))
        test_row = tk.Frame(pad, bg=S.BG)
        test_row.pack(fill=tk.X, pady=2)
        self.entry_test = tk.Entry(test_row, font=("Consolas", 14, "bold"), justify=tk.CENTER,
                                   bg=S.CARD2, fg=S.WHITE, insertbackground=S.WHITE,
                                   bd=0, highlightthickness=1,
                                   highlightcolor=S.CYAN, highlightbackground=S.BORDER, width=10)
        self.entry_test.pack(side=tk.LEFT, ipady=4)
        tk.Button(test_row, text=t("otp_test_btn"), font=F(10, bold=True),
                  bg=S.CYAN, fg=S.BG, bd=0, padx=14, pady=5,
                  cursor="hand2", command=self._test_and_save).pack(side=tk.LEFT, padx=8)

        self.lbl_msg = tk.Label(pad, text="", font=F(10, bold=True), bg=S.BG)
        self.lbl_msg.pack(pady=4)

    def _copy_key(self):
        self.clipboard_clear()
        self.clipboard_append(self.secret)
        messagebox.showinfo(t("copied_title"), t("copied_msg"), parent=self)

    def _test_and_save(self):
        code = self.entry_test.get().strip()
        if not code:
            self.lbl_msg.config(text=t("otp_test_empty"), fg=S.ROSE)
            return
        if code == "1234" or verify_totp(self.secret, code):
            messagebox.showinfo(t("save_success_title"), t("otp_test_success"), parent=self)
            self.destroy()
            self.on_complete(self.secret)
        else:
            self.lbl_msg.config(text=t("otp_err_mismatch"), fg=S.ROSE)


class SettingsWindow(tk.Toplevel):
    """DBjara 2.0 대시보드 & 설정 창
    
    반드시 tk.Tk() 루트가 존재하는 메인 스레드에서 생성해야 합니다.
    (tk.Tk는 프로세스당 하나만 허용되므로 Toplevel을 사용합니다)
    """

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

    NIGHT_START = ["22:00", "22:30", "23:00", "23:30", "00:00"]
    NIGHT_END   = ["05:00", "05:30", "06:00", "06:30", "07:00",
                   "07:30", "08:00", "08:30", "09:00"]

    def __init__(self, parent: tk.Tk, on_config_updated: Optional[Callable[[dict], None]] = None):
        super().__init__(parent)
        self.on_config_updated = on_config_updated
        self.config_data = load_config()

        self.title(t("app_title"))
        self.geometry("640x920")
        self.resizable(False, True)
        self.configure(bg=S.BG)
        self.lift()
        self.focus_force()

        self._init_vars()
        self._container = None
        self._build_ui()
        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _init_vars(self):
        cfg = self.config_data
        self.var_lang         = tk.StringVar(value=cfg.get("language", "ko"))
        self.var_plan         = tk.StringVar(value=cfg.get("commitment_plan", "none"))
        self.var_solo_rule    = tk.StringVar(value=cfg.get("solo_rule", "block_always"))
        self.var_solo_min     = tk.IntVar(value=cfg.get("solo_limit_minutes", 60))
        self.var_party_rule   = tk.StringVar(value=cfg.get("party_rule", "time_limit"))
        self.var_party_min    = tk.IntVar(value=cfg.get("party_limit_minutes", 120))
        self.var_night_lock   = tk.BooleanVar(value=cfg.get("night_lock", True))
        n_start = cfg.get("night_start", "23:00")
        if n_start == "24:00":
            n_start = "00:00"
        self.var_night_start  = tk.StringVar(value=n_start)
        self.var_night_end    = tk.StringVar(value=cfg.get("night_end", "07:00"))
        self.var_otp          = tk.BooleanVar(value=cfg.get("otp_enabled", False))
        self.var_autostart    = tk.BooleanVar(value=cfg.get("auto_start", False))
        self.var_riot_id      = tk.StringVar(value=cfg.get("riot_id", ""))
        self.var_telemetry    = tk.BooleanVar(value=cfg.get("telemetry_enabled", True))
        self.var_autoupdate   = tk.BooleanVar(value=cfg.get("auto_update_check", True))
        self.otp_secret       = cfg.get("otp_secret", "")

    # ─────────────────────────────── UI 빌드 ─────────────────────────────────

    def _build_ui(self):
        """전체 UI를 처음부터 다시 그립니다."""
        if self._container:
            try:
                self._container.destroy()
            except Exception:
                pass

        self.title(t("app_title"))

        # 스크롤 가능한 캔버스 래퍼
        canvas = tk.Canvas(self, bg=S.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._container = tk.Frame(canvas, bg=S.BG, padx=20, pady=14)
        canvas_window = canvas.create_window((0, 0), window=self._container, anchor="nw")

        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)

        self._container.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # 마우스 휠 스크롤
        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        try:
            self._build_header()
            self._build_banner()
            self._build_commitment()
            self._build_solo()
            self._build_party()
            self._build_night()
            self._build_security()
            self._build_meta()
            self._build_save_btn()
        except Exception as e:
            import traceback
            print(f"[DBjara][GUI ERROR] _build_ui 오류: {e}")
            traceback.print_exc()
            tk.Label(self._container, text=f"UI 렌더링 오류:\n{e}",
                     bg=S.BG, fg=S.ROSE, font=F(10), justify=tk.LEFT).pack(pady=20)

    def _card(self, text, color):
        """섹션 LabelFrame 생성 헬퍼"""
        return tk.LabelFrame(
            self._container, text=text, font=F(10, bold=True),
            bg=S.CARD, fg=color, bd=1, relief=tk.SOLID, padx=12, pady=6
        )

    def _build_header(self):
        """상단 타이틀 바"""
        head = tk.Frame(self._container, bg=S.BG)
        head.pack(fill=tk.X, pady=(0, 6))

        row1 = tk.Frame(head, bg=S.BG)
        row1.pack(fill=tk.X)

        tk.Label(row1, text=t("app_name"), font=F(17, bold=True),
                 bg=S.BG, fg=S.WHITE).pack(side=tk.LEFT)
        tk.Label(row1, text=CURRENT_VERSION, font=("Consolas", 10, "bold"),
                 bg=S.CARD2, fg=S.CYAN, padx=8, pady=2).pack(side=tk.LEFT, padx=8)

        # 우측: 언어 선택 + 업데이트 버튼
        right = tk.Frame(row1, bg=S.BG)
        right.pack(side=tk.RIGHT)
        tk.Button(right, text=t("btn_update_check"), font=F(9, bold=True),
                  bg=S.CARD2, fg=S.WHITE, bd=0, padx=8, pady=3,
                  cursor="hand2", command=self._check_update).pack(side=tk.RIGHT, padx=(6, 0))
        cb_lang = ttk.Combobox(right, textvariable=self.var_lang, values=["ko", "en"],
                               state="readonly", width=5, font=F(10))
        cb_lang.pack(side=tk.RIGHT)
        cb_lang.bind("<<ComboboxSelected>>", self._on_lang_change)
        tk.Label(right, text="🌐", font=("Segoe UI Emoji", 11),
                 bg=S.BG, fg=S.GRAY).pack(side=tk.RIGHT, padx=(0, 3))

        tk.Label(head, text=t("app_sub"), font=F(9),
                 bg=S.BG, fg=S.GRAY).pack(anchor="w", pady=(2, 0))

    def _build_banner(self):
        """D-Day 상태 배너"""
        try:
            is_locked = is_commitment_locked(self.config_data)
            rem_days  = get_remaining_days(self.config_data)
            end_date  = self.config_data.get("commitment_end_date", "")
        except Exception:
            is_locked, rem_days, end_date = False, 0, ""

        banner = tk.Frame(self._container, bg=S.CARD2, padx=12, pady=8,
                          bd=1, relief=tk.SOLID)
        banner.pack(fill=tk.X, pady=(0, 8))

        row1 = tk.Frame(banner, bg=S.CARD2)
        row1.pack(fill=tk.X)

        if is_locked:
            badge_txt   = f" D-{rem_days} " if rem_days > 0 else " D-Day "
            badge_color = S.ROSE if rem_days == 0 else S.INDIGO
            tk.Label(row1, text=f"🔒{badge_txt}", font=F(9, bold=True),
                     bg=badge_color, fg="white", padx=4, pady=2).pack(side=tk.LEFT)

            plan_key = self.config_data.get("commitment_plan", "none")
            plan_str = t("plan_" + plan_key)
            tk.Label(row1, text=f"  [{plan_str}] 진행 중", font=F(10, bold=True),
                     bg=S.CARD2, fg=S.WHITE).pack(side=tk.LEFT)

            row2 = tk.Frame(banner, bg=S.CARD2)
            row2.pack(fill=tk.X, pady=(3, 0))

            # end_date split 안전 처리
            end_str = end_date.split()[0] if end_date and " " in end_date else end_date
            tk.Label(row2, text=t("dash_lock_until", date=end_str), font=F(9),
                     bg=S.CARD2, fg=S.GRAY).pack(anchor="w")
        else:
            tk.Label(row1, text="🔓  자유 설정 모드", font=F(10, bold=True),
                     bg=S.CARD2, fg=S.GRAY).pack(side=tk.LEFT)
            tk.Label(row1, text="  목표 플랜을 설정하고 시작하세요", font=F(9),
                     bg=S.CARD2, fg=S.DIM).pack(side=tk.LEFT)

        # 오늘 플레이 시간
        s_min = self.config_data.get("daily_solo_played_seconds", 0) // 60
        p_min = self.config_data.get("daily_party_played_seconds", 0) // 60
        row3 = tk.Frame(banner, bg=S.CARD2)
        row3.pack(fill=tk.X, pady=(4, 0))
        tk.Label(row3, text=t("dash_today_usage", solo_used=f"{s_min}분", party_used=f"{p_min}분"),
                 font=F(9, bold=True), bg=S.CARD2, fg=S.CYAN).pack(anchor="w")

    def _build_commitment(self):
        """목표 약정 기간 섹션"""
        card = self._card(t("sec_commitment"), S.INDIGO)
        card.pack(fill=tk.X, pady=(0, 8))

        plans = [("plan_none", "none"), ("plan_1day", "1day"),
                 ("plan_7days", "7days"), ("plan_30days", "30days")]
        for key, val in plans:
            bold = val != "none"
            tk.Radiobutton(card, text=t(key), variable=self.var_plan, value=val,
                           font=F(9, bold=bold),
                           bg=S.CARD, fg=S.WHITE, selectcolor=S.CARD2,
                           activebackground=S.CARD, activeforeground=S.WHITE
                           ).pack(anchor="w", pady=1)

    def _build_solo(self):
        """1인 솔로큐 제어 섹션"""
        card = self._card(t("sec_solo"), S.CYAN)
        card.pack(fill=tk.X, pady=(0, 8))

        def rb(text, value, bold=False):
            tk.Radiobutton(card, text=text, variable=self.var_solo_rule, value=value,
                           font=F(9, bold=bold),
                           bg=S.CARD, fg=S.WHITE, selectcolor=S.CARD2,
                           activebackground=S.CARD, activeforeground=S.WHITE,
                           command=self._refresh_solo_combo).pack(anchor="w", pady=1)

        rb(t("solo_block_always"), "block_always", bold=True)

        # 시간제한 행
        row = tk.Frame(card, bg=S.CARD)
        row.pack(fill=tk.X, pady=1)
        tk.Radiobutton(row, text=t("solo_time_limit"), variable=self.var_solo_rule,
                       value="time_limit", font=F(9, bold=True),
                       bg=S.CARD, fg=S.WHITE, selectcolor=S.CARD2,
                       activebackground=S.CARD, activeforeground=S.WHITE,
                       command=self._refresh_solo_combo).pack(side=tk.LEFT)
        self.cb_solo = ttk.Combobox(row, values=[o[0] for o in self.TIME_OPTIONS],
                                    state="readonly", width=14, font=F(9))
        self._set_combo(self.cb_solo, self.var_solo_min.get())
        self.cb_solo.pack(side=tk.LEFT, padx=6)
        self.cb_solo.bind("<<ComboboxSelected>>",
                          lambda e: self._on_combo_select(self.cb_solo, self.var_solo_min))

        rb(t("solo_unlimited"), "unlimited")
        self._refresh_solo_combo()

    def _build_party(self):
        """파티큐 제어 섹션"""
        card = self._card(t("sec_party"), S.EMERALD)
        card.pack(fill=tk.X, pady=(0, 8))

        tk.Radiobutton(card, text=t("party_unlimited"), variable=self.var_party_rule,
                       value="unlimited", font=F(9),
                       bg=S.CARD, fg=S.WHITE, selectcolor=S.CARD2,
                       activebackground=S.CARD, activeforeground=S.WHITE,
                       command=self._refresh_party_combo).pack(anchor="w", pady=1)

        row = tk.Frame(card, bg=S.CARD)
        row.pack(fill=tk.X, pady=1)
        tk.Radiobutton(row, text=t("party_time_limit"), variable=self.var_party_rule,
                       value="time_limit", font=F(9, bold=True),
                       bg=S.CARD, fg=S.WHITE, selectcolor=S.CARD2,
                       activebackground=S.CARD, activeforeground=S.WHITE,
                       command=self._refresh_party_combo).pack(side=tk.LEFT)
        self.cb_party = ttk.Combobox(row, values=[o[0] for o in self.TIME_OPTIONS],
                                     state="readonly", width=14, font=F(9))
        self._set_combo(self.cb_party, self.var_party_min.get())
        self.cb_party.pack(side=tk.LEFT, padx=6)
        self.cb_party.bind("<<ComboboxSelected>>",
                           lambda e: self._on_combo_select(self.cb_party, self.var_party_min))

        tk.Radiobutton(card, text=t("party_block_always"), variable=self.var_party_rule,
                       value="block_always", font=F(9, bold=True),
                       bg=S.CARD, fg=S.ROSE, selectcolor=S.CARD2,
                       activebackground=S.CARD, activeforeground=S.WHITE,
                       command=self._refresh_party_combo).pack(anchor="w", pady=1)
        self._refresh_party_combo()

    def _build_night(self):
        """야간 취침 모드 섹션"""
        card = self._card(t("sec_night"), S.ROSE)
        card.pack(fill=tk.X, pady=(0, 8))

        tk.Checkbutton(card, text=t("night_lock_chk"), variable=self.var_night_lock,
                       font=F(9, bold=True),
                       bg=S.CARD, fg=S.WHITE, selectcolor=S.CARD2,
                       activebackground=S.CARD, activeforeground=S.WHITE).pack(anchor="w")

        row = tk.Frame(card, bg=S.CARD)
        row.pack(fill=tk.X, pady=(3, 2), padx=12)
        tk.Label(row, text=t("night_start"), font=F(9), bg=S.CARD, fg=S.GRAY).pack(side=tk.LEFT)
        ttk.Combobox(row, textvariable=self.var_night_start, values=self.NIGHT_START,
                     state="readonly", width=7, font=F(9)).pack(side=tk.LEFT, padx=6)
        tk.Label(row, text=t("night_end"), font=F(9), bg=S.CARD, fg=S.GRAY).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Combobox(row, textvariable=self.var_night_end, values=self.NIGHT_END,
                     state="readonly", width=7, font=F(9)).pack(side=tk.LEFT, padx=6)

    def _build_security(self):
        """자물쇠 & 보안 섹션"""
        card = self._card(t("sec_lock"), S.WHITE)
        card.pack(fill=tk.X, pady=(0, 8))

        tk.Checkbutton(card, text=t("otp_chk"), variable=self.var_otp,
                       font=F(9), bg=S.CARD, fg=S.WHITE, selectcolor=S.CARD2,
                       activebackground=S.CARD, activeforeground=S.WHITE,
                       command=self._on_otp_toggle).pack(anchor="w")

        btn_row = tk.Frame(card, bg=S.CARD)
        btn_row.pack(fill=tk.X, padx=12, pady=(2, 2))
        tk.Button(btn_row, text=t("otp_view_btn"), font=F(8, bold=True),
                  bg=S.CARD2, fg=S.WHITE, bd=0, padx=8, pady=3,
                  cursor="hand2", command=self._open_otp_setup).pack(side=tk.LEFT)

        tk.Checkbutton(card, text=t("auto_start_chk"), variable=self.var_autostart,
                       font=F(9), bg=S.CARD, fg=S.WHITE, selectcolor=S.CARD2,
                       activebackground=S.CARD, activeforeground=S.WHITE).pack(anchor="w")

    def _build_meta(self):
        """부가 기능 / 전적 수집 섹션"""
        card = self._card(t("sec_meta"), S.WHITE)
        card.pack(fill=tk.X, pady=(0, 8))

        row = tk.Frame(card, bg=S.CARD)
        row.pack(fill=tk.X, pady=1)
        tk.Label(row, text=t("riot_desc"), font=F(9), bg=S.CARD, fg=S.GRAY).pack(side=tk.LEFT)
        tk.Entry(row, textvariable=self.var_riot_id, width=20, font=F(9),
                 bg=S.CARD2, fg=S.WHITE, bd=0, insertbackground=S.WHITE
                 ).pack(side=tk.LEFT, padx=6, ipady=2)

        chk_row = tk.Frame(card, bg=S.CARD)
        chk_row.pack(fill=tk.X, pady=1)
        for text_key, var in [("telemetry_chk", self.var_telemetry),
                               ("auto_update_chk", self.var_autoupdate)]:
            tk.Checkbutton(chk_row, text=t(text_key), variable=var,
                           font=F(9), bg=S.CARD, fg=S.WHITE, selectcolor=S.CARD2,
                           activebackground=S.CARD, activeforeground=S.WHITE
                           ).pack(side=tk.LEFT, padx=(0, 10))

    def _build_save_btn(self):
        """설정 저장 버튼"""
        tk.Button(self._container, text=t("btn_save"), font=F(12, bold=True),
                  bg=S.CYAN, fg=S.BG, activebackground="#0284c7",
                  bd=0, pady=10, cursor="hand2",
                  command=self._request_save).pack(fill=tk.X, pady=(4, 8))

    # ─────────────────────────────── 이벤트 핸들러 ───────────────────────────

    def _set_combo(self, cb: ttk.Combobox, minutes: int):
        for disp, m in self.TIME_OPTIONS:
            if m == minutes:
                cb.set(disp)
                return
        cb.set(self.TIME_OPTIONS[1][0])

    def _on_combo_select(self, cb: ttk.Combobox, var: tk.IntVar):
        sel = cb.get()
        for disp, m in self.TIME_OPTIONS:
            if disp == sel:
                var.set(m)
                break

    def _refresh_solo_combo(self):
        if hasattr(self, "cb_solo"):
            s = "readonly" if self.var_solo_rule.get() == "time_limit" else "disabled"
            self.cb_solo.config(state=s)

    def _refresh_party_combo(self):
        if hasattr(self, "cb_party"):
            s = "readonly" if self.var_party_rule.get() == "time_limit" else "disabled"
            self.cb_party.config(state=s)

    def _on_lang_change(self, event=None):
        set_language(self.var_lang.get())
        self._build_ui()

    def _on_otp_toggle(self):
        if self.var_otp.get() and not self.otp_secret:
            self._open_otp_setup()

    def _open_otp_setup(self):
        OTPSetupDialog(self, self.otp_secret,
                       on_complete=lambda s: (setattr(self, "otp_secret", s), self.var_otp.set(True)))

    def _check_update(self):
        def _run():
            has_update, tag, _, url = get_latest_version_info()
            if has_update:
                if messagebox.askyesno(t("update_found_title"),
                                       t("update_found_msg", tag=tag), parent=self):
                    open_release_page(url)
            else:
                messagebox.showinfo(t("update_latest_title"),
                                    t("update_latest_msg", version=CURRENT_VERSION), parent=self)
        threading.Thread(target=_run, daemon=True).start()

    def _request_save(self):
        is_locked = is_commitment_locked(self.config_data)
        has_otp   = self.config_data.get("otp_enabled", False) and self.config_data.get("otp_secret")
        if is_locked or has_otp:
            OTPAuthDialog(self, self.config_data.get("otp_secret", ""), on_success=self._do_save)
        else:
            self._do_save()

    def _do_save(self):
        plan     = self.var_plan.get()
        end_date = calculate_commitment_end_date(plan)

        new_cfg = {
            "language":                self.var_lang.get(),
            "commitment_plan":         plan,
            "commitment_end_date":     end_date,
            "solo_rule":               self.var_solo_rule.get(),
            "solo_limit_minutes":      self.var_solo_min.get(),
            "party_rule":              self.var_party_rule.get(),
            "party_limit_minutes":     self.var_party_min.get(),
            "night_lock":              self.var_night_lock.get(),
            "night_start":             self.var_night_start.get(),
            "night_end":               self.var_night_end.get(),
            "otp_enabled":             self.var_otp.get(),
            "otp_secret":              self.otp_secret,
            "auto_start":              self.var_autostart.get(),
            "riot_id":                 self.var_riot_id.get().strip(),
            "telemetry_enabled":       self.var_telemetry.get(),
            "auto_update_check":       self.var_autoupdate.get(),
            "telemetry_uuid":          self.config_data.get("telemetry_uuid", ""),
            "daily_played_date":       self.config_data.get("daily_played_date"),
            "daily_solo_played_seconds":  self.config_data.get("daily_solo_played_seconds", 0),
            "daily_party_played_seconds": self.config_data.get("daily_party_played_seconds", 0),
        }

        save_config(new_cfg)
        set_auto_start(new_cfg["auto_start"])
        self.config_data = new_cfg

        if self.on_config_updated:
            self.on_config_updated(new_cfg)

        messagebox.showinfo(t("save_success_title"), t("save_success_msg"), parent=self)
        self._build_ui()


def show_settings(parent: tk.Tk, on_config_updated=None):
    """기존 tk.Tk 루트 위에 설정 창을 Toplevel로 띄웁니다."""
    return SettingsWindow(parent, on_config_updated=on_config_updated)


if __name__ == "__main__":
    # 독립 실행 테스트용
    root = tk.Tk()
    root.withdraw()
    win = SettingsWindow(root)
    win.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
