# Project Plan & Feature Roadmap

> **Project:** Linux Native Markdown Note App (Apple Notes Aesthetic)  
> **Engine:** PyQt6 + Pure File System  
> **Last Updated:** 2026-11-10

---

## 🧭 Status Legend
* 🟢 **`[Completed]`** - Implemented, tested, and verified.
* 🟡 **`[In Progress]`** - Currently under active development.
* ⚪ **`[Planned]`** - Defined and scheduled for upcoming phases.

---

## 📋 Features & Implementation Roadmap

### Phase 1: Tooling, Environment & Scaffolding
* 🟢 **`[Completed]`** **Verify toolchain & venv:** Python 3.14 venv verified with PyQt6 6.12.0.
* 🟢 **`[Completed]`** **Project Directory Scaffolding:** Clean modular architecture created (`core/`, `ui/`, `utils/`).
* 🟢 **`[Completed]`** **Application Entry Point (`main.py`):** High-DPI, dark theme initialization and clean lifecycle.

---

### Phase 2: Core Storage & File-System Engine (`core/`)
* 🟢 **`[Completed]`** **Pure File-System Architecture (`~/Documents/Notes/`):**
  * Auto-creates root storage directory on first launch.
  * Subdirectories map directly to folders in the app sidebar (zero database).
* 🟢 **`[Completed]`** **Note Data Model (`core/note.py`):**
  * Title extracted dynamically from the first non-empty line.
  * 2-line preview snippet cleaned and parsed.
  * Relative timestamp formatting (*"Just now"*, *"10:45 AM"*, *"Yesterday"*).
* 🟢 **`[Completed]`** **Storage Manager (`core/storage.py`):**
  * Safe atomic file writing (temporary file replace to prevent corruption).
  * Debounced auto-save (saves in background 400ms after user pauses typing).
  * File renaming when the first line changes.
  * Safe deletion (moves to `.trash`).
* ⚪ **`[Planned]`** **External File Watcher:**
  * Use `QFileSystemWatcher` to detect when notes are modified externally.

---

### Phase 3: The 3-Pane Apple Notes UI Layout (`ui/`)
* 🟢 **`[Completed]`** **Collapsible 3-Column Splitter (`ui/main_window.py`):**
  * Fluid `QSplitter` with preserved column proportions.
  * Sidebar toggle shortcut (`Ctrl+\`).
* 🟢 **`[Completed]`** **Folders Sidebar (`ui/sidebar.py`):**
  * Tree view displaying "All Notes" and custom subfolders matching the filesystem.
  * "New Folder" inline creation button.
* 🟢 **`[Completed]`** **Note Cards List (`ui/note_list.py`):**
  * Custom card view (`QStyledItemDelegate`):
    * Bold note title.
    * Formatted relative timestamp.
    * 2-line preview snippet.
    * Smooth pill selection highlight.
  * "New Note" action (`Ctrl+N`).
* 🟢 **`[Completed]`** **Apple Notes Visual Styling (`ui/theme.py`):**
  * Clean, distraction-free dark aesthetic with subtle borders and rounded cards.

---

### Phase 4: Obsidian-Style In-Editor Live Preview & Interactive Checkboxes (`ui/editor.py`)
* ⚪ **`[Planned]`** **Live In-Editor Markdown Formatting:**
  * No separate preview window or split screen: styling happens directly on the editor canvas.
  * Headings (H1, H2, H3) automatically scale in font size and visual hierarchy.
  * Bold, italic, blockquotes, and code blocks styled cleanly in-place.
  * Generous document margins and clean, readable typography.
* ⚪ **`[Planned]`** **Interactive Checkboxes:**
  * Detect `- [ ]` and `- [x]` markdown checklist items.
  * Render interactive, clickable checkbox icons in-place.
  * Clicking with the mouse immediately toggles check/uncheck state, applies strikethrough styling to completed text, and saves to the markdown file.

---

### Phase 5: Floating Slash (`/`) Command Palette (`ui/slash_menu.py`)
* ⚪ **`[Planned]`** **Trigger Detection:**
  * Detect when `/` is typed at the start of a line or after whitespace.
* ⚪ **`[Planned]`** **Floating Cursor-Aligned Popup:**
  * Calculate exact pixel coordinates of the text cursor (`cursorRect()`).
  * Display a lightweight, frameless floating menu directly under the cursor.
* ⚪ **`[Planned]`** **Real-Time Search & Markdown Actions:**
  * 🔤 **Heading 1 / 2 / 3** (`# `, `## `, `### `)
  * ☑️ **To-do Checkbox** (`- [ ] `)
  * 📋 **Bulleted List** (`- `)
  * 🔢 **Numbered List** (`1. `)
  * 💻 **Code Block** (```` ``` ````)
  * 💬 **Quote** (`> `)
  * ➖ **Horizontal Divider** (`---`)
* ⚪ **`[Planned]`** **Seamless Keyboard Control:**
  * Filter as you type (`/h1`, `/todo`, etc.).
  * `Up` / `Down` arrows to navigate, `Enter` to insert, `Escape` to dismiss.

---

### Phase 6: Search, Polish & Shortcuts
* ⚪ **`[Planned]`** **Instant Real-Time Search:**
  * Search bar above note list filters notes instantaneously by title and body content.
* ⚪ **`[Planned]`** **Productivity Keyboard Shortcuts:**
  * `Ctrl+N`: New note.
  * `Ctrl+Shift+N`: New folder.
  * `Ctrl+\`: Toggle sidebar.
  * `Ctrl+F`: Jump to search bar.
  * `Ctrl+D`: Delete current note.
* ⚪ **`[Planned]`** **Linux Integration:**
  * Standard XDG folder compliance (`~/.config/note-taker/` for settings).
  * Native desktop launcher entry (`note-taker.desktop`).
