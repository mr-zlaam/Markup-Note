"""Automated test for Note Export to PDF and HTML."""

import shutil
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPainter

from core.storage import StorageManager
from ui.main_window import MainWindow
from ui.theme import apply_theme
from utils.exporter import export_note_to_html, export_note_to_pdf


def run_tests() -> None:
    test_dir = Path(tempfile.mkdtemp(prefix="export_test_"))
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        apply_theme(app)

        window = MainWindow()
        window.resize(1100, 750)
        window.show()

        window.storage = StorageManager(root_dir=test_dir)
        window._current_folder = None
        window.config_manager.config_dir = test_dir / ".config"

        # 1. Setup Note
        note = window.storage.create_note()
        assert note is not None
        window._refresh_notes(preserve_path=str(note.path), emit_selection=True)
        app.processEvents()

        editor_panel = window.editor
        sample_title = "Quantum Physics Overview"
        sample_markdown = """# Quantum Physics Overview

Quantum mechanics is a fundamental theory in physics that describes the behavior of matter and energy.

## Key Principles
- **Superposition:** Particles exist in multiple states simultaneously.
- **Entanglement:** Measurement of one particle correlates instantly with another.
- **Wave-Particle Duality:** Entities exhibit both wave and particle characteristics.

### Checklist
- [x] Review Schrödinger equation
- [ ] Implement Bloch sphere simulation
- [ ] Prepare lecture slides

### Example Matrix Equation
```python
import numpy as np

psi = np.array([1, 0], dtype=complex)
H = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]])
result = np.dot(H, psi)
print("Superposed state:", result)
```

> "If you think you understand quantum mechanics, you don't understand quantum mechanics." — Richard Feynman
"""
        editor_panel.title_edit.setText(sample_title)
        editor_panel.editor.setPlainText(sample_markdown)
        app.processEvents()

        assert editor_panel.export_btn.isEnabled(), "Export button should be enabled when note is loaded"
        print("Export button state: PASS (Enabled)")

        # 2. Test PDF Export
        print("Testing PDF Export...")
        pdf_out = test_dir / "quantum_note.pdf"
        ok_pdf = export_note_to_pdf(sample_title, sample_markdown, pdf_out)
        assert ok_pdf, "export_note_to_pdf should return True"
        assert pdf_out.exists(), f"PDF file {pdf_out} should exist"
        assert pdf_out.stat().st_size > 5000, f"PDF file size should be substantial (got {pdf_out.stat().st_size} bytes)"

        # Check PDF header bytes (%PDF)
        with open(pdf_out, "rb") as f:
            header_bytes = f.read(5)
            assert header_bytes == b"%PDF-", f"Expected %PDF- header, got {header_bytes}"
        print(f"PDF Export: PASS (Valid PDF generated, {pdf_out.stat().st_size} bytes)")

        # 3. Test HTML Export (Light Theme)
        print("Testing HTML Export (Light)...")
        html_light_out = test_dir / "quantum_note_light.html"
        ok_html_light = export_note_to_html(sample_title, sample_markdown, html_light_out, dark_theme=False)
        assert ok_html_light, "export_note_to_html (light) should return True"
        assert html_light_out.exists()
        content_light = html_light_out.read_text(encoding="utf-8")
        assert "<title>Quantum Physics Overview</title>" in content_light
        assert "Superposition" in content_light
        assert "Richard Feynman" in content_light
        assert "--bg-color: #ffffff" in content_light
        print(f"HTML Light Export: PASS (Valid HTML, {html_light_out.stat().st_size} bytes)")

        # 4. Test HTML Export (Dark Theme)
        print("Testing HTML Export (Dark)...")
        html_dark_out = test_dir / "quantum_note_dark.html"
        ok_html_dark = export_note_to_html(sample_title, sample_markdown, html_dark_out, dark_theme=True)
        assert ok_html_dark, "export_note_to_html (dark) should return True"
        assert html_dark_out.exists()
        content_dark = html_dark_out.read_text(encoding="utf-8")
        assert "--bg-color: #1e1e22" in content_dark
        assert "--text-color: #e2e2e8" in content_dark
        print(f"HTML Dark Export: PASS (Valid Dark HTML, {html_dark_out.stat().st_size} bytes)")

        # 5. Visual Capture
        print("Capturing editor header with Export button...")
        win_pix = window.grab()
        out_path = Path("/home/redhats/.gemini/antigravity/brain/70ac962d-bada-4915-826a-b9cd14afaf61/verified_export_button.png")
        win_pix.save(str(out_path), "PNG")
        print(f"Screenshot saved to {out_path}")

        window.close()
        print("ALL EXPORT TESTS PASSED WITH 100% SUCCESS!")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    run_tests()
