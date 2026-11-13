# Contributing to Markup Notes

Thank you for your interest in contributing to Markup Notes. This document outlines guidelines for reporting issues, proposing features, and contributing code.

---

## Philosophy

Markup Notes is built on three core principles:
1. **Lightweight and Fast:** Native Python and PyQt6 execution with zero Chromium or Electron overhead.
2. **Local-First and Private:** Notes are plain Markdown files on your local filesystem with optional Git version control. No proprietary cloud locks.
3. **First-Class Linux Desktop Integration:** Clean, responsive behavior across Wayland and X11 compositors (GNOME, KDE Plasma, Niri, Hyprland, COSMIC).

All contributions should respect these principles.

---

## Reporting Bugs

Before submitting a bug report:
1. Check existing open and closed issues to avoid duplicate reports.
2. Verify you are running the latest release or main branch.

When opening an issue:
* Use the **Bug Report** template.
* Include your Linux distribution (e.g., Fedora, Arch Linux, Ubuntu).
* Include your display server session type (**Wayland** or **X11**).
* Include your desktop environment or compositor (e.g., Niri, GNOME, KDE Plasma, Hyprland).
* Attach visual evidence (a screen recording in `.mp4` or `.webm`, or screenshots) whenever possible, especially for UI or rendering bugs.
* Paste terminal logs or tracebacks in the designated code block if available.

---

## Suggesting Enhancements

Feature requests are welcome:
* Use the **Feature Request** template.
* Clearly describe the problem you want to solve and your proposed solution.
* Keep in mind the lightweight, distraction-free focus of Markup Notes. Heavy external dependencies or features requiring background cloud daemons are generally avoided.

---

## Development Setup

### Prerequisites
* Linux (Wayland or X11)
* Python 3.10 or newer
* `git`
* Recommended: `uv` package manager (or standard `venv` and `pip`)

### Clone and Install
```bash
git clone https://github.com/mr-zlaam/MarkupNotes.git
cd MarkupNotes

# Option A: Using uv (fastest)
uv sync
uv run python3 main.py

# Option B: Standard Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python3 main.py
```

### Running Tests
Ensure tests pass before opening a pull request:
```bash
pytest
```

---

## Code Guidelines

1. **Architecture & Separation of Concerns:**
   * Keep UI components (`ui/`), business logic (`core/`), and utility helpers (`utils/`) strictly decoupled.
   * Do not place reusable helper functions directly inside UI classes. Use the `utils/` directory.

2. **Typing and Code Quality:**
   * Use Python type annotations (`typing.Optional`, `typing.List`, `typing.Dict`, `Path`, etc.) for function signatures and public APIs.
   * Follow PEP 8 naming standards (`snake_case` for methods/variables, `PascalCase` for classes).
   * Do not use bare `except:` clauses. Catch specific exceptions.

3. **Atomic File Writes:**
   * Any file saving or modification must use atomic file operations (writing to a temporary file first before replacement) to protect user data from corruption.

4. **Style and Content Constraints:**
   * Do not add emojis to code comments, commit messages, documentation, or pull request descriptions. Maintain clean, professional, plain text styling.

---

## Pull Request Process

1. Fork the repository and create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Commit your changes with clear, descriptive commit messages.
3. Test your changes locally under Wayland and/or X11 to ensure no regressions.
4. Push your branch to your fork and open a pull request against the `main` branch.
5. In your pull request description, explain the motivation for the change and provide steps for reviewers to test it.
