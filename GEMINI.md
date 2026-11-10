# Project Rules & Best Practices

## 🚨 Critical Gatekeeper Rule (Mandatory)

> **The "Dance" Authorization Rule:**
> You are **strictly prohibited** from making any code changes, creating new code files, editing existing files, or modifying any project files **UNLESS** the user explicitly includes the word **`dance`** (case-insensitive) in their prompt.
>
> * **If `dance` is NOT in the prompt:** You must strictly act in discussion, planning, architectural design, analysis, and advisory mode. Do NOT edit, touch, delete, or create any code files.
> * **If `dance` IS in the prompt:** You are authorized to proceed with the requested code implementation and file edits, while adhering to all best practices outlined below.

---

## 🐍 Python & Project Best Practices

### 1. Architecture & Design
* **Separation of Concerns:** Keep UI (`ui/`), business logic (`core/`), and data storage/IO (`storage/`) strictly decoupled.
* **Lightweight First:** Avoid heavy third-party dependencies when standard library or PyQt6 built-ins suffice.
* **Single Responsibility Principle (SRP):** Each class and module should have one clearly defined responsibility.
* **No Premature Optimization, but Avoid Known Pitfalls:** Keep data structures in memory efficient (e.g., slotted classes or dataclasses for note items).

### 2. Typing & Code Clarity
* **Type Annotations:** Use Python type hints (`typing.Optional`, `typing.List`, `typing.Dict`, `Path`, etc.) for all function signatures and public APIs.
* **PEP 8 Standards:** Adhere to standard Python naming conventions:
  * `snake_case` for functions, methods, and variables.
  * `PascalCase` for classes.
  * `SCREAMING_SNAKE_CASE` for constants.
* **Descriptive Naming:** Avoid single-letter variables except for common iteration indices (`i`, `j`) or coordinate points (`x`, `y`).
* **Docstrings:** Provide concise docstrings for all modules, classes, and non-trivial functions.

### 3. Error Handling & Robustness
* **No Bare Exceptions:** Never write `except: pass` or catch generic `Exception` without logging or targeted recovery. Catch specific errors (e.g., `FileNotFoundError`, `PermissionError`, `UnicodeDecodeError`).
* **Graceful Degradation:** File I/O errors or parsing errors must never crash the UI; surface clear, non-intrusive status messages to the user.
* **Atomic File Writes:** When saving notes, write to a temporary file first and atomic-replace to prevent file corruption on system crash or sudden power loss.

### 4. PyQt6 & GUI Best Practices
* **Keep the GUI Thread Responsive:**
  * Never perform blocking file scanning or network I/O directly inside the main UI event loop.
  * Use `QThread` / `QThreadPool` / `QRunnable` for heavy tasks if processing large directories.
* **Proper Qt Object Ownership:** Always pass parent widgets (`parent=self`) to child widgets and layouts to prevent memory leaks and dangling C++ pointers.
* **Signal/Slot Discipline:** Use Qt's new-style signals (`pyqtSignal`) and avoid circular signal emissions.
* **Debounce Auto-Save:** Protect disk I/O by debouncing text changes (e.g., `QTimer.singleShot(400, ...)`).

### 5. Packaging & Environment
* **Virtual Environments Only:** Work exclusively within the project's virtual environment (`.venv`).
* **Clean Dependencies:** Keep `pyproject.toml` minimal and lock versions reliably.
* **Cross-Desktop Native Feel:** Respect standard Linux desktop specifications (XDG base directories for config/cache: `~/.config/`, `~/.local/share/`).
### 6. Separate the concerns
* **Never write utility functions:** Never write utility methods or functions in logic directly there will be always separate directory for all utils and reusable code.