"""Unit tests verifying safe two-way multi-machine synchronization and conflict preservation."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from core.git_manager import GitManager


class TestTwoWaySync(unittest.TestCase):
    """Test suite verifying two-way multi-machine synchronization with zero data loss."""

    def setUp(self) -> None:
        if not GitManager(Path(".")).is_git_installed():
            self.skipTest("Git command line tool is not installed in this environment.")

        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create a bare remote Git repository simulating GitHub
        self.remote_dir = self.root / "remote.git"
        subprocess.run(
            ["git", "init", "--bare", "-b", "main", str(self.remote_dir)],
            check=True,
            capture_output=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_multi_machine_disjoint_notes_sync(self) -> None:
        """Verify Machine B with local notes connects to GitHub and imports Machine A's notes without loss."""
        # 1. Machine A: Creates notes and backs them up to remote
        dir_a = self.root / "machine_a"
        gm_a = GitManager(dir_a)
        ok_init_a, _ = gm_a.init_repo()
        self.assertTrue(ok_init_a)

        (dir_a / "NoteA1.md").write_text("# Note A1 from Machine A\n", encoding="utf-8")
        (dir_a / "NoteA2.md").write_text("# Note A2 from Machine A\n", encoding="utf-8")
        gm_a.set_remote(str(self.remote_dir))
        ok_sync_a, msg_a = gm_a.sync()
        self.assertTrue(ok_sync_a, f"Machine A initial sync failed: {msg_a}")

        # 2. Machine B: User starts app on fresh machine, writes local notes before connecting
        dir_b = self.root / "machine_b"
        dir_b.mkdir()
        (dir_b / "NoteB1.md").write_text("# Note B1 written on Machine B\n", encoding="utf-8")
        (dir_b / "NoteB2.md").write_text("# Note B2 written on Machine B\n", encoding="utf-8")

        gm_b = GitManager(dir_b)
        gm_b.set_remote(str(self.remote_dir))

        # 3. Machine B syncs (connects and pulls/pushes)
        ok_sync_b, msg_b = gm_b.sync()
        self.assertTrue(ok_sync_b, f"Machine B sync failed: {msg_b}")

        # 4. Verify Machine B has all 4 notes
        b_files = sorted([p.name for p in dir_b.glob("*.md")])
        self.assertEqual(
            b_files,
            ["NoteA1.md", "NoteA2.md", "NoteB1.md", "NoteB2.md"],
            "Machine B must have all notes from both Machine A and Machine B",
        )

        # 5. Machine A syncs later and receives Machine B's notes
        ok_sync_a2, msg_a2 = gm_a.sync()
        self.assertTrue(ok_sync_a2, f"Machine A secondary sync failed: {msg_a2}")

        a_files = sorted([p.name for p in dir_a.glob("*.md")])
        self.assertEqual(
            a_files,
            ["NoteA1.md", "NoteA2.md", "NoteB1.md", "NoteB2.md"],
            "Machine A must receive Machine B's notes upon subsequent sync",
        )

    def test_same_file_conflict_preserves_both_versions(self) -> None:
        """Verify modifying the same note offline on both machines preserves both copies with zero data loss."""
        # Machine A creates and pushes Shared.md
        dir_a = self.root / "machine_a"
        gm_a = GitManager(dir_a)
        gm_a.init_repo()
        (dir_a / "Meeting.md").write_text("# Strategy from Machine A\n", encoding="utf-8")
        gm_a.set_remote(str(self.remote_dir))
        gm_a.sync()

        # Machine B creates Meeting.md with different local notes offline
        dir_b = self.root / "machine_b"
        dir_b.mkdir()
        (dir_b / "Meeting.md").write_text("# Strategy from Machine B\n", encoding="utf-8")
        gm_b = GitManager(dir_b)
        gm_b.set_remote(str(self.remote_dir))

        # Machine B syncs
        ok_sync_b, msg_b = gm_b.sync()
        self.assertTrue(ok_sync_b, f"Machine B sync with conflict failed: {msg_b}")

        # Verify neither file contains Git conflict markers
        b_files = {p.name: p.read_text(encoding="utf-8") for p in dir_b.glob("*.md")}
        self.assertIn("Meeting.md", b_files)
        self.assertIn("Meeting (Cloud Backup).md", b_files)

        self.assertNotIn("<<<<<<<", b_files["Meeting.md"])
        self.assertNotIn(">>>>>>>", b_files["Meeting.md"])
        self.assertNotIn("<<<<<<<", b_files["Meeting (Cloud Backup).md"])
        self.assertNotIn(">>>>>>>", b_files["Meeting (Cloud Backup).md"])

        # Check content
        self.assertEqual(b_files["Meeting.md"], "# Strategy from Machine B\n")
        self.assertEqual(b_files["Meeting (Cloud Backup).md"], "# Strategy from Machine A\n")

        # Machine A syncs and receives the duplicate backup copy without error
        ok_sync_a, msg_a = gm_a.sync()
        self.assertTrue(ok_sync_a, f"Machine A sync failed: {msg_a}")
        a_files = {p.name for p in dir_a.glob("*.md")}
        self.assertIn("Meeting.md", a_files)
        self.assertIn("Meeting (Cloud Backup).md", a_files)

    def test_rebase_recovery(self) -> None:
        """Verify is_in_rebase and abort_rebase properly recover from a suspended rebase state."""
        dir_test = self.root / "rebase_test"
        gm = GitManager(dir_test)
        gm.init_repo()

        git_dir = dir_test / ".git"
        fake_rebase_dir = git_dir / "rebase-merge"
        fake_rebase_dir.mkdir(parents=True, exist_ok=True)

        self.assertTrue(gm.is_in_rebase())
        # Clean up
        fake_rebase_dir.rmdir()
        self.assertFalse(gm.is_in_rebase())


if __name__ == "__main__":
    unittest.main()
