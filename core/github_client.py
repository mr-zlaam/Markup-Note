"""GitHub API client handling OAuth token verification, private repo setup, and profile metadata."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from utils.paths import get_config_dir
from storage.credential_store import CredentialStore


@dataclass
class GitHubUser:
    """Authenticated GitHub user profile."""

    login: str
    name: str = ""
    avatar_url: str = ""
    html_url: str = ""


@dataclass
class GitHubRepo:
    """GitHub repository representation."""

    name: str
    full_name: str
    private: bool
    clone_url: str
    html_url: str


class GitHubClient:
    """Lightweight zero-dependency GitHub API client using Python's standard library."""

    GITHUB_API_BASE = "https://api.github.com"
    USER_AGENT = "MarkupNotes-App/1.0"
    TOKEN_GENERATE_URL = "https://github.com/settings/tokens/new?scopes=repo&description=Markup+Notes"

    def __init__(self, config_dir: Optional[Path] = None, check_cli_fallback: Optional[bool] = None) -> None:
        self.config_dir = config_dir if config_dir is not None else get_config_dir()
        self.auth_file = self.config_dir / "github_auth.json"
        self.check_cli_fallback = check_cli_fallback if check_cli_fallback is not None else (config_dir is None)
        self.credential_store = CredentialStore(config_dir=self.config_dir)

    def get_token(self) -> Optional[str]:
        """Retrieve stored GitHub token from secure credential storage (migrating plaintext tokens if present)."""
        # 1. Automatic migration: if a legacy plaintext token exists in github_auth.json, move it to CredentialStore
        if self.auth_file.exists():
            try:
                data = json.loads(self.auth_file.read_text(encoding="utf-8"))
                legacy_token = data.get("token")
                if legacy_token and str(legacy_token).strip():
                    self.credential_store.save_token(str(legacy_token).strip())
                    del data["token"]
                    self.auth_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
                    try:
                        os.chmod(self.auth_file, 0o600)
                    except OSError:
                        pass
            except (OSError, json.JSONDecodeError):
                pass

        # 2. Retrieve token from secure credential store
        token = self.credential_store.get_token()
        if token:
            return token

        # 3. Fallback to active GitHub CLI session if configured
        if self.check_cli_fallback:
            gh_token = self._get_gh_cli_token()
            if gh_token:
                return gh_token

        return None

    def save_token(
        self,
        token: str,
        login: str = "",
        repo_url: str = "",
    ) -> bool:
        """Persist GitHub token securely into CredentialStore and save non-sensitive metadata to disk."""
        token_clean = token.strip()
        if not token_clean:
            return False

        # 1. Save secret token into secure credential storage
        ok_secret = self.credential_store.save_token(token_clean)

        # 2. Persist profile metadata (WITHOUT the secret token) to local config
        self.config_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "login": login.strip(),
            "repo_url": repo_url.strip(),
        }
        try:
            temp_path = self.auth_file.with_suffix(".tmp")
            temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            try:
                os.chmod(temp_path, 0o600)
            except OSError:
                pass
            temp_path.replace(self.auth_file)
            return ok_secret
        except OSError:
            return False

    def clear_token(self) -> bool:
        """Remove stored credentials and profile metadata on sign-out."""
        self.credential_store.delete_token()
        if self.auth_file.exists():
            try:
                self.auth_file.unlink()
                return True
            except OSError:
                return False
        return True

    def get_stored_profile(self) -> Tuple[Optional[str], Optional[str]]:
        """Return (login, repo_url) if saved locally."""
        if not self.auth_file.exists():
            return (None, None)
        try:
            data = json.loads(self.auth_file.read_text(encoding="utf-8"))
            return (data.get("login"), data.get("repo_url"))
        except (OSError, json.JSONDecodeError):
            return (None, None)

    def _get_gh_cli_token(self) -> Optional[str]:
        """Attempt to fetch token from system GitHub CLI (`gh auth token`) if installed."""
        if not shutil.which("gh"):
            return None
        try:
            res = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except (subprocess.TimeoutExpired, PermissionError, OSError):
            pass
        return None

    def _api_request(
        self,
        endpoint: str,
        token: str,
        method: str = "GET",
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, Any, str]:
        """Perform authenticated HTTP request to GitHub API via urllib."""
        url = f"{self.GITHUB_API_BASE}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token.strip()}",
            "Accept": "application/vnd.github+json",
            "User-Agent": self.USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        }

        body_bytes: Optional[bytes] = None
        if json_data is not None:
            headers["Content-Type"] = "application/json"
            body_bytes = json.dumps(json_data).encode("utf-8")

        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                code = resp.getcode()
                raw_body = resp.read().decode("utf-8")
                parsed = json.loads(raw_body) if raw_body else {}
                return (code, parsed, "")
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("message", f"HTTP {exc.code}")
            except Exception:
                msg = err_body or f"HTTP {exc.code}"
            return (exc.code, None, msg)
        except urllib.error.URLError as exc:
            return (0, None, f"Network error: {exc.reason}")
        except Exception as exc:
            return (0, None, str(exc))

    def verify_token(self, token: str) -> Tuple[bool, Optional[GitHubUser], str]:
        """Verify GitHub token validity and retrieve authenticated user profile."""
        if not token.strip():
            return (False, None, "Token cannot be empty.")

        code, data, err = self._api_request("/user", token=token)
        if code == 200 and isinstance(data, dict):
            user = GitHubUser(
                login=data.get("login", ""),
                name=data.get("name", "") or data.get("login", ""),
                avatar_url=data.get("avatar_url", ""),
                html_url=data.get("html_url", ""),
            )
            return (True, user, "Token verified successfully.")

        if code == 401:
            return (False, None, "GitHub token is invalid or expired. Please generate a new token.")

        return (False, None, err or f"Verification failed with status {code}")

    def create_private_repo(
        self,
        token: str,
        repo_name: str = "markup-notes",
        description: str = "My Markup Notes vault",
    ) -> Tuple[bool, Optional[GitHubRepo], str]:
        """Create a new private repository on the user's GitHub account."""
        payload = {
            "name": repo_name,
            "private": True,
            "description": description,
            "auto_init": False,
        }
        code, data, err = self._api_request("/user/repos", token=token, method="POST", json_data=payload)

        if code in (201, 200) and isinstance(data, dict):
            repo = GitHubRepo(
                name=data.get("name", repo_name),
                full_name=data.get("full_name", f"/{repo_name}"),
                private=data.get("private", True),
                clone_url=data.get("clone_url", ""),
                html_url=data.get("html_url", ""),
            )
            return (True, repo, "Created private repository successfully.")

        # If repo already exists on user's account (HTTP 422)
        if code == 422:
            ok_u, user, _ = self.verify_token(token)
            if ok_u and user:
                code_get, data_get, _ = self._api_request(f"/repos/{user.login}/{repo_name}", token=token)
                if code_get == 200 and isinstance(data_get, dict):
                    repo = GitHubRepo(
                        name=data_get.get("name", repo_name),
                        full_name=data_get.get("full_name", ""),
                        private=data_get.get("private", True),
                        clone_url=data_get.get("clone_url", ""),
                        html_url=data_get.get("html_url", ""),
                    )
                    return (True, repo, f"Repository '{repo_name}' already exists and connected.")

        return (False, None, err or f"Failed to create repository ({code})")

    def build_authenticated_remote_url(self, clone_url: str, token: str = "") -> str:
        """Return clean remote clone URL without embedding plaintext credentials.

        Authentication is handled dynamically in-memory during git operations via askpass,
        ensuring tokens are never persisted in .git/config on disk.
        """
        parsed = urllib.parse.urlparse(clone_url.strip())
        if parsed.scheme in ("http", "https"):
            netloc = parsed.hostname or ""
            if parsed.port:
                netloc += f":{parsed.port}"
            return urllib.parse.urlunparse(
                (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
            )
        return clone_url.strip()
