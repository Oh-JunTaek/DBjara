"""
DBjara - TOTP (시간 기반 일회용 비밀번호) 엔진
RFC 6238 / RFC 4226 표준 알고리즘을 파이썬 내장 라이브러리로 구현한 모듈입니다.
"""

import hmac
import hashlib
import time
import struct
import base64
import secrets
import string


def generate_secret(length: int = 16) -> str:
    """무작위 Base32 비밀키를 생성합니다."""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _get_hotp_token(secret: str, intervals_no: int, digits: int = 6) -> str:
    """주어진 카운터 인터벌에 대한 HOTP 토큰을 계산합니다."""
    # 비밀키 정규화 (공백 제거 및 대문자 변환)
    clean_secret = secret.replace(" ", "").upper()
    # Base32 패딩 보정
    padding = len(clean_secret) % 8
    if padding != 0:
        clean_secret += "=" * (8 - padding)

    key = base64.b32decode(clean_secret)
    msg = struct.pack(">Q", intervals_no)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[19] & 15
    h_int = struct.unpack(">I", h[o : o + 4])[0] & 0x7FFFFFFF
    token = str(h_int % (10**digits)).zfill(digits)
    return token


def get_totp_token(secret: str, interval: int = 30, digits: int = 6) -> str:
    """현재 시간을 기반으로 6자리 TOTP 번호를 생성합니다."""
    current_step = int(time.time() // interval)
    return _get_hotp_token(secret, current_step, digits)


def verify_totp(
    secret: str, code: str, interval: int = 30, window: int = 1, digits: int = 6
) -> bool:
    """
    입력된 TOTP 번호의 유효성을 검증합니다.
    window=1은 앞뒤 30초의 시간 오차를 허용합니다.
    """
    if not secret or not code:
        return False

    code = code.strip()
    if not code.isdigit() or len(code) != digits:
        return False

    current_step = int(time.time() // interval)
    for offset in range(-window, window + 1):
        if _get_hotp_token(secret, current_step + offset, digits) == code:
            return True
    return False


def get_otpauth_uri(
    secret: str, account_name: str = "User", issuer: str = "DBjara"
) -> str:
    """Google Authenticator 등 OTP 앱 등록을 위한 otpauth:// URI를 생성합니다."""
    return f"otpauth://totp/{issuer}:{account_name}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"


if __name__ == "__main__":
    # 자체 테스트
    key = generate_secret()
    token = get_totp_token(key)
    print(f"생성된 비밀키: {key}")
    print(f"현재 번호: {token}")
    print(f"검증 결과: {verify_totp(key, token)}")
    print(f"인증 URI: {get_otpauth_uri(key)}")
