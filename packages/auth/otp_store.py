"""In-memory OTP store with 5-minute TTL.

In dev mode the OTP is printed to the terminal so the admin can read it.
To plug in your NestJS OTP service, replace the body of `dispatch_otp`
in packages/auth/service.py with a call to your existing endpoint.
"""

import random
import threading
import time
from dataclasses import dataclass


@dataclass
class _Entry:
    otp: str
    expires_at: float


_store: dict[str, _Entry] = {}
_lock = threading.Lock()

_OTP_TTL = 300  # 5 minutes


def create(phone: str) -> str:
    otp = str(random.randint(100000, 999999))
    with _lock:
        _store[phone] = _Entry(otp=otp, expires_at=time.time() + _OTP_TTL)
    return otp


def verify(phone: str, otp: str) -> bool:
    with _lock:
        entry = _store.get(phone)
        if not entry:
            return False
        if time.time() > entry.expires_at:
            del _store[phone]
            return False
        if entry.otp != otp:
            return False
        del _store[phone]
        return True
