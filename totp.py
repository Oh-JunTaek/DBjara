"""
TOTP (Time-based One-Time Password) Engine
RFC 6238 / RFC 4226 implementation using standard Python libraries.
"""

import hmac
import hashlib
import time
import struct
import base64
import secrets
import string


def generate_secret(length: int = 16) -> str:
    """Generate a random Base32 secret key."""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _get_hotp_token(secret: str, intervals_no: int, digits: int = 6) -> str:
    """Calculate HOTP token for a given counter interval."""
    # Normalize secret (remove spaces, upper case)
    clean_secret = secret.replace(" ", "").upper()
    # Add padding if necessary
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
    """Get current TOTP token based on current time."""
    current_step = int(time.time() // interval)
    return _get_hotp_token(secret, current_step, digits)


def verify_totp(
    secret: str, code: str, interval: int = 30, window: int = 1, digits: int = 6
) -> bool:
    """
    Verify TOTP token.
    window=1 allows +-30 seconds clock drift.
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
    secret: str, account_name: str = "User", issuer: str = "dbjara"
) -> str:
    """Generate otpauth:// URI for Google Authenticator QR Code scanning."""
    return f"otpauth://totp/{issuer}:{account_name}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"


if __name__ == "__main__":
    # Self-test
    key = generate_secret()
    token = get_totp_token(key)
    print(f"Generated Secret: {key}")
    print(f"Current Token: {token}")
    print(f"Verification: {verify_totp(key, token)}")
    print(f"Auth URI: {get_otpauth_uri(key)}")
