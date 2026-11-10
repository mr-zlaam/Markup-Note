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
* 🟢 **`[Completed]`** **Cursor-Aware Live Markdown Formatting (`ui/highlighter.py`):**
  * Pure plain-text buffer (`toPlainText()` / `setPlainText()`)—never mutates or escapes user text.
  * Real-time `MarkdownHighlighter` scaling headers (H1: 24pt, H2: 19pt, H3: 16pt, H4: 14pt).
  * Automatically hides markdown syntax markers (`# `, `**`, `*`, `` ` ``, `~~`, `> `, `[](url)`) as soon as the cursor leaves the line, and reveals them when the cursor returns to the line.
* 🟢 **`[Completed]`** **Interactive Checkboxes:**
  * Click on `- [ ]` / `- [x]` immediately toggles state with dimmed text styling (`#787880`, no strikethrough line crossing).
  * `Ctrl+Enter` shortcut to toggle current line checkbox or convert line into a checkbox.
  * Smart `Enter` auto-continuation for checklists and bulleted/numbered lists.
  * `Tab` / `Shift+Tab` 2-space indentation.
* 🟢 **`[Completed]`** **Interactive Links & Hover Actions:**
  * Hovering over links (`[label](url)`) displays a pointing hand cursor and tooltip (`Ctrl+Click or Ctrl+Enter to open <url>`).
  * `Ctrl+Click` or pressing `Ctrl+Enter` when on a link opens the URL in the system default web browser.
* 🟢 **`[Completed]`** **Advanced Markdown: Styled Vector Tables (`utils/table.py`):**
  * Auto-formatting pipe tables with column alignment (`:---`, `:---:`, `---:`), alternating rows, and rounded card styling.
  * Natural column auto-sizing without artificial 240px clipping.
  * Native horizontal scrolling for wide tables (wheel, trackpad horizontal swipe, Shift+Wheel, or dragging the scrollbar thumb).
  * `Tab` to navigate cells, `Shift+Tab` to go to previous cell, `Enter` to auto-continue rows or auto-generate header separators.
  * Mathematical notation cleanup in table cards (`Aᵀ`, `A⁻¹`, `det(A)`, `tr(A)`, `λᵢ`, `Iₙ`, `O(n²)`).
* 🟢 **`[Completed]`** **Advanced Markdown: Syntax-Highlighted Code Cards (`utils/code_engine.py`):**
  * macOS-style rounded cards with 3 window control dots (`#ff5f56`, `#ffbd2e`, `#27c93f`), language badge, and monospaced syntax coloring.
  * One-click "Copy" button in the header bar with emerald green "Copied!" feedback and system clipboard synchronization.
  * Native horizontal scrolling for long code lines with subtle scrollbar indicator.
* 🟢 **`[Completed]`** **Advanced Markdown: LaTeX Math Typesetting (`utils/math_engine.py`):**
  * Offline pure-Python recursive-descent math parser and typesetter.
  * Delimiters: standard LaTeX `\[ ... \]` / `\\[ ... \\]` (display) and `\( ... \)` / `\\( ... \\)` (inline) in addition to `$$...$$` and `$..$`.
  * `\boxed{...}` equation borders, `\mathbf{...}` bold glyphs/vectors, `bmatrix`, `pmatrix`, `vmatrix`.
  * Fractions, roots, subscripts/superscripts, unescaped markdown subscripts (`\_`), Greek symbols, and big operators (`∑`, `∫`, `∏`, `lim`).
* 🟢 **`[Completed]`** **Bullet Lists & Ordered Lists Hierarchy & Navigation:**
  * Cursor-aware Live Preview: Inactive bullet items render as vector bullet glyphs (`•` solid circle at level 0, `◦` hollow ring at level 1, `▪` solid square at level 2+) rather than raw ASCII hyphens.
  * Reveals raw markdown (`- `, `* `, `+ `) in bold blue (`#0a84ff`) when cursor is placed on the line.
  * Ordered lists (`1. `, `2) `) cleanly styled with bold Apple blue markers (`#0a84ff`).
  * Smart `Tab` / `Shift+Tab`: Indents / unindents list and checkbox lines by 2 spaces at the start of the block; also handles multi-line selections.
  * Smart `Enter`: Auto-continues bullets and auto-increments numbered lists (`1.` -> `2.`, `1)` -> `2)`); unindents indented items when empty and terminates top-level empty items to exit cleanly.
  * Smart `Backspace`: When pressed right after empty marker (`- `, `1. `), deletes marker or unindents.
  * Full nesting and hierarchy support inside blockquotes (`> - item`, `> 1. item`).

---

### Phase 5: Floating Slash (`/`) Command Palette (`ui/slash_menu.py`) *(Deferred until after core editor stabilization)*
* ⚪ **`[Planned]`** **Trigger Detection:**
  * Detect `/` typed at the start of a line.
* ⚪ **`[Planned]`** **Floating Cursor-Aligned Popup:**
  * Float cleanly directly under the text cursor.
* ⚪ **`[Planned]`** **Real-Time Search & Markdown Actions:**
  * Filter across H1, H2, H3, To-do Checkbox, Bullet list, Numbered list, Code block, Quote, and Divider.
* ⚪ **`[Planned]`** **Seamless Keyboard Control:**
  * `Up` / `Down` arrows to navigate, `Enter` to insert, `Escape` to dismiss.

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
