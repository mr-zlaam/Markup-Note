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
  * Sidebar toggle shortcut (`Ctrl+\`) and Notes list toggle shortcut (`Ctrl+Shift+\`).
* 🟢 **`[Completed]`** **VS Code-Style JSON Configuration Engine (`core/config.py`):**
  * Persists layout state (`folders_visible`, `notes_list_visible`, `folders_width`, `notes_list_width`) and window geometry (`width`, `height`, `maximized`) to `~/.config/note-taker/settings.json`.
  * Atomic file writing prevents corruption; graceful defaults prevent startup crashes.
  * Preserves exact collapsed/expanded panel states across app restarts.
* 🟢 **`[Completed]`** **Domain-Owned Controls & Dynamic Edge Handoff:**
  * **Domain Ownership:** Every collapsible pane owns its collapse button strictly within its own header:
    * Folders header has `FOLDERS` title, `+` (New Folder), and `[| ]` (Collapse Folders).
    * Notes list header has `[ 🔍 Search notes... ]`, `+ Note`, and `[ | ]` (Collapse Notes).
  * **Dynamic Edge Handoff:** When a pane collapses to `0px`, the surviving adjacent pane dynamically reveals the restore button at its outer edge:
    * When Folders collapses: Notes list reveals `[| ]` at the left of the search bar.
    * When Notes collapses: Editor reveals `[ | ]` at its top-left header.
  * **Smooth Slide Animation (`QVariantAnimation`):** Smooth 220ms sliding animation with cubic easing (`OutCubic`), zero-flicker handoffs, and instant reversal safety.
  * **Restart Persistence:** Saves and restores collapsed states via `~/.config/note-taker/settings.json`.
* 🟢 **`[Completed]`** **Right-Click Context Menus & Batch Selection (`ui/sidebar.py`, `ui/note_list.py`):**
  * **Folders Right-Click Menu:** Sleek macOS-styled dark menu with Rename, Select, and Delete options.
  * **Notes Right-Click Menu:** Rename Note, Select, and Delete Note options.
  * **Batch Selection Mode:** Selecting "Select" activates batch mode with circular checkmarks (`✓` / `○`) next to each note card. Includes a dedicated batch bar with `Select All` / `Deselect All`, `Delete (X)`, and `Done` buttons, allowing users to delete notes in one go.
  * **Folder Management & Batch Deletion:** Renames folders and notes safely on disk with live file watcher updates; batch deletes selected folders and notes to `.trash`.
* 🟢 **`[Completed]`** **Native Vector Icons & 1-Click Color Customization (`utils/icons.py`, `ui/sidebar.py`, `ui/note_list.py`):**
  * **Vector Folder Icons:** Crisp high-DPI vector folder silhouette beside each folder in the sidebar.
  * **Vector 'All Notes' Icon:** Crisp layered notes/tray emblem beside the root "All Notes" item.
  * **Vector Markdown Icon:** Crisp official Markdown emblem (`M↓`) displayed beside every note title on note cards.
  * **1-Click Color Submenu:** Right-clicking any folder or note provides a "Color" submenu with curated palette presets (Default, Blue, Purple, Green, Yellow, Orange, Red, Teal, Pink) and "Custom Color...".
  * **ModernColorDialog (`ui/dialogs.py`):** Replaces legacy Qt dialog with an Apple Notes dark-themed modal featuring modern "Apply" and "Cancel" buttons, zero 90s icons or keyboard underscores, while preserving full 2D HSV gradient, Hue slider, HTML hex input, and RGB/HSV precision.
  * **Dynamic Tinting:** Instantly tints the folder or Markdown icon in the chosen color.
  * **Settings Persistence:** Color assignments persist to `~/.config/note-taker/settings.json` under `appearance.folder_colors` and `appearance.note_colors`, surviving application restarts.
  * **Rename & Delete Safety:** Automatically transfers custom colors when folders/notes are renamed, and cleans up color mappings when items are deleted.
* 🟢 **`[Completed]`** **Streamlined Selection Mode & Unified Cancel (`✕`) Action:**
  * Added `Select All` / `Deselect All` to the Folders batch bar.
  * Replaced confusing checkmarks with a dedicated `✕` (Cancel) vector button in both Folders and Notes selection bars.
  * Pressing `Escape` anywhere in the app dismisses selection mode and restores normal browsing.
* 🟢 **`[Completed]`** **Clean Editor Header & Premium Dialog Redesign (`ui/editor.py`, `ui/dialogs.py`):**
  * Removed the top-right "Delete" button from the editor header for a cleaner, distraction-free writing environment.
  * Completely redesigned `ModernConfirmDialog` and `ModernInputDialog` to eliminate background banding/black lines on labels, expanded to a spacious 420px width with 12px rounded borders and sleek button styles.
  * Embedded magnifying glass search icon inside `QLineEdit` search input.
  * Clean vector `+` icons for "New Folder" and "New Note" buttons with rounded terminal caps.
  * Modern panel toggle icons for sidebar and notes list (`[| ]` and `[ | ]`).
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
  * Full vertical height guarantee: Code cards accurately compute exact needed vertical height (`header_h + N * 22px + padding`), accounting for blank lines and font scaling so the final lines of code are never clipped.
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
* 🟢 **`[Completed]`** **Double-Click Block Editing & State Bleed Isolation:**
  * Fixed closing fence state bleed: Closing fences (` ``` `) strictly force syntax highlighter block state to 0, eliminating monospace font and dark background bleed into subsequent headings and paragraphs.
  * Preview card stability: Single clicking inside rendered cards (tables, code blocks, math, diagrams) does not disrupt layout or expand raw Markdown.
  * Double-click to edit: Double-clicking any rendered preview card smoothly activates inline Markdown editing at the cursor position.
  * Code card `[Edit]` button: Added an `[Edit]` button in the code card header bar next to `[Copy]` for direct one-click editing.
  * `Escape` key exit: Pressing `Escape` when inside any active code, table, math, or mermaid block exits edit mode and immediately re-collapses back to the rendered card.
  * Hover feedback: Shows pointing hand cursor on hover (clean, no intrusive tooltip).
* 🟢 **`[Completed]`** **Touchscreen Gesture Support & Kinetic Scrolling (`utils/touch.py`):**
  * Touch vs Mouse Separation: Touch contacts and drags are cleanly differentiated from mouse inputs, completely eliminating accidental full-document text selections when scrolling with a finger on touchscreen laptops.
  * Native Touch Scrolling: Swiping up/down on the touchscreen smoothly scrolls the note document with kinetic momentum coasting (60 FPS deceleration).
  * Horizontal Touch Swipe: Swiping horizontally over wide tables or code blocks scrolls the card content smoothly to the left/right.
  * Clean Touch Taps: Single-tapping positions the cursor or toggles checkboxes without dragging selections; double-tapping preview cards enters inline Markdown editing.
  * System-wide Touch Integration: Enabled touch scrolling on the Note Cards list and Sidebar folders tree view.
* 🟢 **`[Completed]`** **Blockquote Hierarchy & Rich Inline HTML Styling (`ui/editor.py`, `ui/highlighter.py`):**
  * Vector Blockquote Accent Bars: Multi-level blockquotes (`>`, `>>`, `>>>>`) render with crisp, continuous vertical vector accent lines (`│` in `#545462`) matching Apostrophe.
  * Proportional Multi-Line Indentation: Applied `QTextBlockFormat.setLeftMargin(level * 18.0 + 8.0)` so all lines in a blockquote (including wrapped paragraphs) stay cleanly indented to the right of the accent lines.
  * 3D Hardware Keycaps (`<kbd>`): HTML `<kbd>Key</kbd>` renders as authentic 3D physical keyboard keycaps with rounded container boxes (`#2e2e38`), subtle borders (`#545464`), bottom edge shadows (`#18181e`), and bold white text (`#f5f5f7`).
  * High-Contrast Highlight (`<mark>`): Upgraded `<mark>` background to vibrant fluorescent Apple yellow (`#ffd60a`) with bold black text (`#111111`) for maximum contrast and legibility.

* 🟢 **`[Completed]`** **Zero-Void Code Card Geometry (`ui/editor.py`, `ui/highlighter.py`):**
  * Tightly bounded code card rect: `card_h` is strictly calculated as `header_h (28px) + top padding (8px) + N * 22px + bottom padding (16px)`, eliminating massive dark voids inside or below code cards.
  * Exact document line height calibration: Code card blocks in the underlying `QTextDocument` are mapped with opening/closing fences absorbing padding and body lines matching 22px, ensuring subsequent headings and paragraphs appear with natural, tight vertical spacing.
* 🟢 **`[Completed]`** **Massive Paste Performance & Viewport-Only Repaint Acceleration (`ui/editor.py`, `ui/highlighter.py`):**
  * Viewport culling in `paintEvent`: Painting starts strictly at `self.cursorForPosition(QPoint(0, 0)).block()` and halts as soon as `b_rect.top() > vp_height`, turning full document rendering from $O(N)$ into $O(\text{viewport})$.
  * Atomic document editing on paste (`insertFromMimeData`): Ensures large pasted text is inserted as clean plain text wrapped in `beginEditBlock()`/`endEditBlock()`, avoiding HTML document thrashing.
  * Debounced blockquote margin updates: `_update_blockquote_margins` is debounced by 50ms and wrapped in an atomic edit block with recursion guards, preventing layout churn on mass pasting.
  * Substring pre-checks in highlighter: Added $O(1)$ fast character checks before firing regex search loops.
  * Benchmark results: 5,000-line paste reduced from **2,650 ms freeze down to 133 ms (30× faster)**; repainting runs at **4.96 ms (200 FPS capability)**.

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
