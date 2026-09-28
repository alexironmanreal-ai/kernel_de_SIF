# -*- coding: utf-8 -*-
"""Seguridad: hashing bcrypt, políticas de contraseña, tokens."""
from __future__ import annotations
import re
import secrets
import string
import hashlib
from dataclasses import dataclass
from typing import Tuple

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False


@dataclass
class PasswordPolicy:
    min_length: int = 12
    require_upper: bool = True
    require_lower: bool = True
    require_digit: bool = True
    require_special: bool = True
    special_chars: str = "!@#$%^&*()-_=+[]{}|;:,.<>?"

    def validate(self, password: str) -> Tuple[bool, str]:
        if len(password) < self.min_length:
            return False, f"Mínimo {self.min_length} caracteres"
        if self.require_upper and not re.search(r"[A-Z]", password):
            return False, "Requiere mayúscula"
        if self.require_lower and not re.search(r"[a-z]", password):
            return False, "Requiere minúscula"
        if self.require_digit and not re.search(r"\d", password):
            return False, "Requiere dígito"
        if self.require_special and not any(c in self.special_chars for c in password):
            return False, "Requiere carácter especial"
        return True, "OK"

    def generate(self, length: int = 16) -> str:
        alphabet = string.ascii_letters + string.digits + self.special_chars
        while True:
            pwd = "".join(secrets.choice(alphabet) for _ in range(length))
            ok, _ = self.validate(pwd)
            if ok:
                return pwd


def hash_password(password: str) -> str:
    if HAS_BCRYPT:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"sha256${salt}${h}"


def verify_password(password: str, stored: str) -> bool:
    if HAS_BCRYPT and not stored.startswith("sha256$"):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
        except Exception:
            return False
    if stored.startswith("sha256$"):
        _, salt, h = stored.split("$", 2)
        return hashlib.sha256((salt + password).encode("utf-8")).hexdigest() == h
    # legacy v2
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == stored


def generate_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)
