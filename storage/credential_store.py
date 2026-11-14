"""Secure credential storage utilizing system keyring with encrypted local fallback."""

from __future__ import annotations

import getpass
import hashlib
import hmac
import json
import os
from pathlib import Path
import platform
from typing import Optional

from utils.paths import get_config_dir


class CredentialStore:
    """Manages secret credentials (such as GitHub PATs) securely.

    Primary storage: OS native secret service via standard Python `keyring` (GNOME Keyring,
    KWallet, Secret Service API).
    Fallback storage: Authenticated encrypted vault with 0600 POSIX permissions when a keyring
    daemon is not present or inaccessible in minimal desktop environments.
    """

    SERVICE_NAME = "io.github.mr_zlaam.MarkupNotes"
    ACCOUNT_NAME = "github_token"

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        self.config_dir = config_dir if config_dir is not None else get_config_dir()
        self.vault_file = self.config_dir / ".credentials.vault"
        self._keyring_available = self._probe_keyring()

    def _probe_keyring(self) -> bool:
        """Check if Python keyring is installed and has a functional backend."""
        try:
            import keyring
            backend = keyring.get_keyring()
            # If keyring resolves to a fail backend, it is not functional
            backend_name = backend.__class__.__name__.lower()
            if "fail" in backend_name or "null" in backend_name:
                return False
            return True
        except (ImportError, Exception):
            return False

    def get_token(self) -> Optional[str]:
        """Retrieve stored GitHub token from keyring or fallback vault."""
        # 1. Try system keyring first if available
        if self._keyring_available:
            try:
                import keyring
                token = keyring.get_password(self.SERVICE_NAME, self.ACCOUNT_NAME)
                if token and token.strip():
                    return token.strip()
            except Exception:
                # Keyring daemon communication failure; fallback to vault
                pass

        # 2. Fallback to local encrypted vault
        return self._read_vault_token()

    def save_token(self, token: str) -> bool:
        """Persist GitHub token securely into keyring and encrypted vault."""
        token_clean = token.strip()
        if not token_clean:
            return False

        keyring_success = False
        if self._keyring_available:
            try:
                import keyring
                keyring.set_password(self.SERVICE_NAME, self.ACCOUNT_NAME, token_clean)
                keyring_success = True
            except Exception:
                keyring_success = False

        # Always maintain the local vault as an encrypted backup for offline/daemonless sessions
        vault_success = self._write_vault_token(token_clean)

        return keyring_success or vault_success

    def delete_token(self) -> bool:
        """Delete stored GitHub token from both keyring and local vault."""
        keyring_deleted = True
        if self._keyring_available:
            try:
                import keyring
                keyring.delete_password(self.SERVICE_NAME, self.ACCOUNT_NAME)
            except Exception:
                # If already deleted or keyring unavailable, ignore
                keyring_deleted = False

        vault_deleted = self._clear_vault()
        return keyring_deleted or vault_deleted

    # --------------------------------------------------------------------------
    # Fallback Encrypted Vault (PBKDF2 + HMAC-SHA256 Authenticated Keystream)
    # --------------------------------------------------------------------------

    def _derive_vault_key(self) -> bytes:
        """Derive host-specific encryption key based on machine identity and user profile."""
        machine_id = "markup-notes-host"
        for candidate in (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id")):
            if candidate.exists() and candidate.is_file():
                try:
                    content = candidate.read_text(encoding="utf-8").strip()
                    if content:
                        machine_id = content
                        break
                except OSError:
                    continue

        salt = hashlib.sha256(f"{machine_id}:{platform.node()}".encode("utf-8")).digest()
        user_seed = f"{getpass.getuser()}:{Path.home()}".encode("utf-8")
        return hashlib.pbkdf2_hmac("sha256", user_seed, salt, iterations=100000)

    def _read_vault_token(self) -> Optional[str]:
        """Decrypt and verify token from local vault file."""
        if not self.vault_file.exists():
            return None

        try:
            raw_bytes = self.vault_file.read_bytes()
            if len(raw_bytes) < 48:
                return None

            iv = raw_bytes[:16]
            expected_mac = raw_bytes[16:48]
            ciphertext = raw_bytes[48:]

            key = self._derive_vault_key()
            mac_key = hashlib.sha256(key + b":mac").digest()
            cipher_key = hashlib.sha256(key + b":cipher" + iv).digest()

            actual_mac = hmac.new(mac_key, iv + ciphertext, hashlib.sha256).digest()
            if not hmac.compare_digest(expected_mac, actual_mac):
                return None

            # Decrypt via keystream
            keystream = bytearray()
            counter = 0
            while len(keystream) < len(ciphertext):
                block = hashlib.sha256(cipher_key + counter.to_bytes(4, "big")).digest()
                keystream.extend(block)
                counter += 1

            plaintext = bytes(c ^ k for c, k in zip(ciphertext, keystream[:len(ciphertext)]))
            data = json.loads(plaintext.decode("utf-8"))
            token = data.get("token")
            return str(token).strip() if token else None
        except (OSError, ValueError, json.JSONDecodeError):
            return None

    def _write_vault_token(self, token: str) -> bool:
        """Encrypt and atomically save token into vault file with 0600 permissions."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            payload = json.dumps({"token": token.strip()}).encode("utf-8")

            iv = os.urandom(16)
            key = self._derive_vault_key()
            mac_key = hashlib.sha256(key + b":mac").digest()
            cipher_key = hashlib.sha256(key + b":cipher" + iv).digest()

            keystream = bytearray()
            counter = 0
            while len(keystream) < len(payload):
                block = hashlib.sha256(cipher_key + counter.to_bytes(4, "big")).digest()
                keystream.extend(block)
                counter += 1

            ciphertext = bytes(p ^ k for p, k in zip(payload, keystream[:len(payload)]))
            mac = hmac.new(mac_key, iv + ciphertext, hashlib.sha256).digest()

            final_data = iv + mac + ciphertext

            # Atomic write with 0600 mode
            temp_path = self.vault_file.with_suffix(".tmp")
            temp_path.write_bytes(final_data)
            try:
                os.chmod(temp_path, 0o600)
            except OSError:
                pass
            temp_path.replace(self.vault_file)
            return True
        except OSError:
            return False

    def _clear_vault(self) -> bool:
        """Remove encrypted vault file."""
        if self.vault_file.exists():
            try:
                self.vault_file.unlink()
                return True
            except OSError:
                return False
        return True
