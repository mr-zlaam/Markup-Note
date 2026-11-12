"""Core Git management module for local note versioning and remote backup sync."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import List, Optional, Tuple


@dataclass
class GitCommit:
    """Represents a single snapshot commit in the Git version history."""

    hash: str
    short_hash: str
    author: str
    relative_date: str
    message: str
    files_changed: int = 0


@dataclass
class GitStatus:
    """Live state of the local notes repository and pending changes."""

    is_repo: bool = False
    branch: str = "main"
    is_clean: bool = True
    modified: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)
    deleted: List[str] = field(default_factory=list)
    untracked: List[str] = field(default_factory=list)
    ahead: int = 0
    behind: int = 0
    remote_url: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def total_changes(self) -> int:
        """Total count of modified, added, deleted, and untracked note files."""
        return len(self.modified) + len(self.added) + len(self.deleted) + len(self.untracked)


class GitManager:
    """Encapsulates all Git repository commands, status checks, diffing, and synchronization."""

    DEFAULT_GITIGNORE = (
        "# Markup Notes standard ignore rules\n"
        ".DS_Store\n"
        "Thumbs.db\n"
        "*~\n"
        "*.tmp\n"
        ".trash/\n"
        ".cache/\n"
    )

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path.resolve()

    def _run_git(self, args: List[str], timeout: int = 15) -> Tuple[int, str, str]:
        """Execute a git subcommand in repo_path with timeout and error handling."""
        if not self.is_git_installed():
            return (1, "", "Git is not installed on this system.")

        cmd = ["git", *args]
        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return (res.returncode, res.stdout.strip(), res.stderr.strip())
        except subprocess.TimeoutExpired:
            return (124, "", "Git command timed out.")
        except (PermissionError, FileNotFoundError, OSError) as exc:
            return (1, "", str(exc))

    def is_git_installed(self) -> bool:
        """Check if git executable is available in PATH."""
        return bool(shutil.which("git"))

    def is_repo(self) -> bool:
        """Check if self.repo_path contains an initialized .git repository."""
        return (self.repo_path / ".git").is_dir()

    def init_repo(self) -> Tuple[bool, str]:
        """Initialize Git repository in self.repo_path with main branch and default .gitignore."""
        if not self.is_git_installed():
            return (False, "Git command-line tool is not installed.")

        self.repo_path.mkdir(parents=True, exist_ok=True)

        # 1. git init -b main
        code, out, err = self._run_git(["init", "-b", "main"])
        if code != 0:
            # Fallback for older git versions that don't support -b
            code, out, err = self._run_git(["init"])
            if code != 0:
                return (False, err or "Failed to initialize Git repository.")

        # 2. Write default .gitignore if not present
        gitignore_path = self.repo_path / ".gitignore"
        if not gitignore_path.exists():
            try:
                gitignore_path.write_text(self.DEFAULT_GITIGNORE, encoding="utf-8")
            except OSError:
                pass

        # 3. Configure local identity fallback if global user identity is missing
        code_u, out_u, _ = self._run_git(["config", "user.name"])
        if code_u != 0 or not out_u:
            self._run_git(["config", "user.name", "Markup Notes"])
            self._run_git(["config", "user.email", "notes@local"])

        # 4. Stage and commit initial vault structure
        self._run_git(["add", "-A"])
        self._run_git(["commit", "-m", "Initial notes repository setup"])

        return (True, "Repository initialized successfully.")

    def get_status(self) -> GitStatus:
        """Retrieve live Git repository status, branch name, remote, and change lists."""
        if not self.is_git_installed():
            return GitStatus(is_repo=False, error_message="Git is not installed.")

        if not self.is_repo():
            return GitStatus(is_repo=False)

        # 1. Branch name
        code, branch_out, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        branch = branch_out if code == 0 and branch_out else "main"

        # 2. Remote URL
        code_rem, rem_out, _ = self._run_git(["remote", "get-url", "origin"])
        remote_url = rem_out if code_rem == 0 and rem_out else None

        # 3. Status changes via porcelain
        code_st, st_out, err_st = self._run_git(["status", "--porcelain=v1", "-uall"])
        if code_st != 0:
            return GitStatus(is_repo=True, branch=branch, remote_url=remote_url, error_message=err_st)

        modified: List[str] = []
        added: List[str] = []
        deleted: List[str] = []
        untracked: List[str] = []

        if st_out:
            for line in st_out.splitlines():
                if len(line) < 4:
                    continue
                code_x = line[0]
                code_y = line[1]
                path_part = line[3:].strip().strip('"')

                if code_x == "?" and code_y == "?":
                    untracked.append(path_part)
                elif code_x == "D" or code_y == "D":
                    deleted.append(path_part)
                elif code_x == "A" or code_y == "A":
                    added.append(path_part)
                elif "M" in (code_x, code_y):
                    modified.append(path_part)
                else:
                    modified.append(path_part)

        # 4. Ahead / Behind remote
        ahead, behind = 0, 0
        if remote_url:
            code_ab, ab_out, _ = self._run_git(["rev-list", "--left-right", "--count", "HEAD...@{u}"])
            if code_ab == 0 and ab_out:
                parts = ab_out.split()
                if len(parts) == 2:
                    try:
                        ahead = int(parts[0])
                        behind = int(parts[1])
                    except ValueError:
                        pass

        is_clean = len(modified) == 0 and len(added) == 0 and len(deleted) == 0 and len(untracked) == 0

        return GitStatus(
            is_repo=True,
            branch=branch,
            is_clean=is_clean,
            modified=modified,
            added=added,
            deleted=deleted,
            untracked=untracked,
            ahead=ahead,
            behind=behind,
            remote_url=remote_url,
        )

    def stage_and_commit(self, message: Optional[str] = None) -> Tuple[bool, str]:
        """Stage all workspace changes and commit with timestamped or custom message."""
        if not self.is_repo():
            return (False, "Directory is not a Git repository.")

        code_add, _, err_add = self._run_git(["add", "-A"])
        if code_add != 0:
            return (False, f"Failed to stage changes: {err_add}")

        if not message:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            message = f"Backup notes: {ts}"

        code_com, out_com, err_com = self._run_git(["commit", "-m", message])
        if code_com != 0:
            if "nothing to commit" in out_com.lower() or "nothing to commit" in err_com.lower():
                return (True, "Nothing to commit, workspace is up to date.")
            return (False, f"Commit failed: {err_com or out_com}")

        return (True, "Changes committed successfully.")

    def is_in_rebase(self) -> bool:
        """Check if repository is suspended in an unfinished rebase."""
        git_dir = self.repo_path / ".git"
        return (git_dir / "rebase-apply").exists() or (git_dir / "rebase-merge").exists()

    def abort_rebase(self) -> bool:
        """Abort an in-progress rebase to restore a clean branch state."""
        if self.is_in_rebase():
            code, _, _ = self._run_git(["rebase", "--abort"])
            return code == 0
        return True

    def fetch(self, remote: str = "origin") -> Tuple[bool, str]:
        """Fetch latest commits and branches from remote repository."""
        if not self.is_repo():
            return (False, "Not a Git repository.")
        status = self.get_status()
        if not status.remote_url:
            return (False, "No remote repository configured.")
        code, out, err = self._run_git(["fetch", remote, status.branch], timeout=35)
        if code != 0:
            return (False, err or out or "Fetch failed.")
        return (True, out or "Fetched remote updates.")

    def pull(self, remote: str = "origin") -> Tuple[bool, str]:
        """Safely import and merge remote changes with two-way conflict preservation."""
        if not self.is_repo():
            return (False, "Not a Git repository.")

        status = self.get_status()
        if not status.remote_url:
            return (False, "No remote repository configured.")

        # 1. Recover from any stale rebase state
        if self.is_in_rebase():
            self.abort_rebase()

        # 2. Stage and commit any pending local changes first so working tree is clean
        if not status.is_clean:
            ok_com, msg_com = self.stage_and_commit("Local notes backup before syncing")
            if not ok_com:
                return (False, f"Cannot sync: failed to commit local changes ({msg_com})")

        # 3. Fetch from remote
        code_fetch, out_fetch, err_fetch = self._run_git(["fetch", remote, status.branch], timeout=35)
        if code_fetch != 0:
            # If remote branch doesn't exist yet (brand new empty remote repo on GitHub), that's expected
            err_lower = (err_fetch or out_fetch).lower()
            if "couldn't find remote ref" in err_lower or "no tracking" in err_lower:
                return (True, "Remote repository is empty, ready for first push.")
            return (False, f"Fetch failed: {err_fetch or out_fetch}")

        remote_ref = f"{remote}/{status.branch}"

        # 4. Check if local HEAD exists
        code_head, _, _ = self._run_git(["rev-parse", "--verify", "HEAD"])
        if code_head != 0:
            # Local repo has zero commits yet; reset directly to remote branch
            code_reset, _, err_reset = self._run_git(["reset", "--hard", remote_ref])
            if code_reset == 0:
                return (True, "Imported remote notes into fresh vault.")
            return (False, f"Initial import failed: {err_reset}")

        # 5. Check if local HEAD and remote_ref are identical
        code_diff, diff_out, _ = self._run_git(["rev-list", "--count", f"HEAD...{remote_ref}"])
        if code_diff == 0 and diff_out.strip() == "0":
            return (True, "Already up to date with remote.")

        # 6. Try clean rebase first (replays local commits cleanly on top of remote)
        code_reb, out_reb, err_reb = self._run_git(["rebase", remote_ref], timeout=35)
        if code_reb == 0:
            return (True, "Rebased local changes cleanly onto remote.")

        # If rebase encountered a conflict or failed:
        self.abort_rebase()

        # 7. Fallback to 3-way merge with --allow-unrelated-histories
        code_merge, out_merge, err_merge = self._run_git(
            ["merge", "--allow-unrelated-histories", "-m", "Merge notes with cloud backup", remote_ref],
            timeout=35,
        )

        # Check for unmerged / conflicted files
        code_conf, conf_out, _ = self._run_git(["diff", "--name-only", "--diff-filter=U"])
        conflicted_files = [line.strip() for line in conf_out.splitlines() if line.strip()]

        if conflicted_files:
            for c_file in conflicted_files:
                p = Path(c_file)
                if p.name == ".gitignore":
                    self._run_git(["checkout", "--ours", c_file])
                    self._run_git(["add", c_file])
                    continue

                # Preserve local version in current file
                self._run_git(["checkout", "--ours", c_file])

                # Extract remote version into a safe "(Cloud Backup)" duplicate file
                code_show, remote_text, _ = self._run_git(["show", f"{remote_ref}:{c_file}"])
                if code_show == 0:
                    stem = p.stem
                    suffix = p.suffix
                    conflict_filename = f"{stem} (Cloud Backup){suffix}"
                    conflict_path = self.repo_path / p.parent / conflict_filename

                    counter = 2
                    while conflict_path.exists():
                        conflict_filename = f"{stem} (Cloud Backup {counter}){suffix}"
                        conflict_path = self.repo_path / p.parent / conflict_filename
                        counter += 1

                    try:
                        conflict_path.parent.mkdir(parents=True, exist_ok=True)
                        file_content = remote_text if remote_text.endswith("\n") else f"{remote_text}\n"
                        conflict_path.write_text(file_content, encoding="utf-8")
                        self._run_git(["add", str(conflict_path.relative_to(self.repo_path))])
                    except OSError:
                        pass

                self._run_git(["add", c_file])

            # Commit the conflict-free merged state
            self._run_git(["commit", "-m", "Auto-resolved note conflicts by preserving both local and cloud versions"])

        return (True, "Successfully imported and merged remote notes.")

    def push(self, remote: str = "origin") -> Tuple[bool, str]:
        """Push local commits to remote branch."""
        if not self.is_repo():
            return (False, "Not a Git repository.")

        status = self.get_status()
        if not status.remote_url:
            return (False, "No remote repository configured.")

        code, out, err = self._run_git(["push", "-u", remote, status.branch], timeout=35)
        if code != 0:
            return (False, err or out or "Push failed.")
        return (True, out or "Pushed to remote.")

    def sync(self, message: Optional[str] = None) -> Tuple[bool, str]:
        """All-in-one sync: commit local notes, pull and merge remote, and push to GitHub."""
        if not self.is_repo():
            ok_init, msg_init = self.init_repo()
            if not ok_init:
                return (False, msg_init)

        # 1. Stage and commit local notes first
        status = self.get_status()
        if not status.is_clean:
            ok_com, msg_com = self.stage_and_commit(message)
            if not ok_com:
                return (False, msg_com)

        # 2. Pull & merge from remote if configured
        status = self.get_status()
        if status.remote_url:
            ok_pull, msg_pull = self.pull()
            if not ok_pull:
                return (False, f"Pull/Merge failed: {msg_pull}")

        # 3. Push to remote if configured
        if status.remote_url:
            ok_push, msg_push = self.push()
            if not ok_push:
                return (False, f"Merged locally, but push failed: {msg_push}")
            return (True, "Synchronized and backed up to GitHub successfully.")

        return (True, "Notes saved and committed to local history.")

    def get_history(self, limit: int = 25) -> List[GitCommit]:
        """Retrieve recent commit history with hashes, relative dates, and messages."""
        if not self.is_repo():
            return []

        # Use unit separator (0x1f) for unambiguous field splitting
        format_str = "%H%x1f%h%x1f%an%x1f%cr%x1f%s"
        code, out, _ = self._run_git(["log", f"-n{limit}", f"--pretty=format:{format_str}"])
        if code != 0 or not out:
            return []

        commits: List[GitCommit] = []
        for line in out.splitlines():
            parts = line.split("\x1f")
            if len(parts) >= 5:
                commits.append(
                    GitCommit(
                        hash=parts[0],
                        short_hash=parts[1],
                        author=parts[2],
                        relative_date=parts[3],
                        message=parts[4],
                    )
                )
        return commits

    def get_file_diff(self, rel_path: str) -> str:
        """Return unified diff for a modified file or full content for an untracked file."""
        if not self.is_repo():
            return ""

        target_file = self.repo_path / rel_path
        if not target_file.exists():
            return "(File was deleted)"

        # Check if untracked
        code, out, _ = self._run_git(["diff", "HEAD", "--", rel_path])
        if code == 0 and out:
            return out

        # If empty diff from HEAD, check diff against index
        code_idx, out_idx, _ = self._run_git(["diff", "--", rel_path])
        if code_idx == 0 and out_idx:
            return out_idx

        # If untracked, generate pseudo-diff with '+' prefix on each line
        try:
            content = target_file.read_text(encoding="utf-8")
            diff_lines = [f"+ {line}" for line in content.splitlines()]
            return f"--- /dev/null\n+++ {rel_path}\n@@ -0,0 +1,{len(diff_lines)} @@\n" + "\n".join(diff_lines)
        except (OSError, UnicodeDecodeError):
            return "(Binary or unreadable file)"

    def revert_file(self, rel_path: str) -> Tuple[bool, str]:
        """Revert a modified file to HEAD state or delete untracked file."""
        if not self.is_repo():
            return (False, "Not a Git repository.")

        target_file = self.repo_path / rel_path

        # 1. Try checkout from HEAD
        code, out, err = self._run_git(["checkout", "HEAD", "--", rel_path])
        if code == 0:
            return (True, f"Reverted {rel_path} to last backup.")

        # 2. If it was untracked, remove it safely
        if target_file.exists() and target_file.is_file():
            try:
                target_file.unlink()
                return (True, f"Removed untracked note {rel_path}.")
            except OSError as exc:
                return (False, str(exc))

        return (False, err or "Could not revert file.")

    def set_remote(self, url: str, remote_name: str = "origin") -> Tuple[bool, str]:
        """Configure or update the remote repository URL."""
        if not self.is_repo():
            ok, msg = self.init_repo()
            if not ok:
                return (False, msg)

        # Check if remote already exists
        code, _, _ = self._run_git(["remote", "get-url", remote_name])
        if code == 0:
            code_set, _, err_set = self._run_git(["remote", "set-url", remote_name, url.strip()])
        else:
            code_set, _, err_set = self._run_git(["remote", "add", remote_name, url.strip()])

        if code_set != 0:
            return (False, err_set or "Failed to set remote repository.")

        return (True, f"Remote '{remote_name}' set to {url.strip()}")

    def get_remote(self, remote_name: str = "origin") -> Optional[str]:
        """Get the configured remote URL or None."""
        if not self.is_repo():
            return None
        code, out, _ = self._run_git(["remote", "get-url", remote_name])
        return out if code == 0 and out else None
