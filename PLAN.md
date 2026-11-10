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
* 🟢 **`[Completed]`** **External File Watcher:**
  * Uses `QFileSystemWatcher` to detect when notes or folders are modified externally.

---

### Phase 3: The 3-Pane Apple Notes UI Layout (`ui/`)
* 🟢 **`[Completed]`** **Collapsible 3-Column Splitter (`ui/main_window.py`):**
  * Fluid `QSplitter` with preserved column proportions.
  * Sidebar toggle shortcut (`Ctrl+\`).
* 🟢 **`[Completed]`** **Folders Sidebar (`ui/sidebar.py`):**
  * Tree view displaying "All Notes" and custom subfolders matching the filesystem.
  * "New Folder" inline creation button and `Ctrl+Shift+N` shortcut.
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
* 🟢 **`[Completed]`** **Live In-Editor Markdown Formatting:**
  * Real-time `MarkdownHighlighter` scaling headers (H1: 20pt, H2: 17pt, H3: 15pt).
  * In-place styling for bold, italic, code blocks, blockquotes, horizontal rules, tags, and links.
* 🟢 **`[Completed]`** **Interactive Checkboxes:**
  * Click on `- [ ]` / `- [x]` immediately toggles state with instant strikethrough visual feedback.
  * `Ctrl+Enter` shortcut to toggle current line checkbox or convert line into a checkbox.
  * Smart `Enter` auto-continuation for checklists and bulleted/numbered lists.
  * `Tab` / `Shift+Tab` 2-space indentation.

---

### Phase 5: Floating Slash (`/`) Command Palette (`ui/slash_menu.py`)
* 🟢 **`[Completed]`** **Trigger Detection:**
  * Automatically detects `/` typed at the start of a line or after whitespace.
* 🟢 **`[Completed]`** **Floating Cursor-Aligned Popup:**
  * Calculates `cursorRect()` and floats cleanly directly under the text cursor.
* 🟢 **`[Completed]`** **Real-Time Search & Markdown Actions:**
  * Filter as you type across H1, H2, H3, To-do Checkbox, Bullet list, Numbered list, Code block, Quote, and Divider.
* 🟢 **`[Completed]`** **Seamless Keyboard Control:**
  * `Up` / `Down` arrows to navigate, `Enter` to insert, `Escape` or clicking away to dismiss.

---

### Phase 6: Search, Polish & Shortcuts
* 🟢 **`[Completed]`** **Instant Real-Time Search:**
  * Search bar filters notes instantaneously by both title and content.
* 🟢 **`[Completed]`** **Productivity Keyboard Shortcuts:**
  * `Ctrl+N`: New note.
  * `Ctrl+Shift+N`: New folder.
  * `Ctrl+\`: Toggle folders sidebar.
  * `Ctrl+F`: Jump to search bar.
  * `Ctrl+D`: Delete current note.
  * `Ctrl+Enter`: Toggle checkbox.
* 🟢 **`[Completed]`** **Linux Integration:**
  * Standard XDG folder compliance (`~/.config/note-taker/`).
  * Desktop application launcher (`note-taker.desktop`).
