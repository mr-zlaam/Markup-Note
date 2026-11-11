"""Runtime diagnostics and graceful crash reporting for Markup Notes."""

import os
import platform
import sys
from typing import Dict


def get_system_diagnostic_info() -> Dict[str, str]:
    """Collect platform, architecture, and glibc versions for debugging."""
    info: Dict[str, str] = {
        "Python": sys.version.split()[0],
        "Platform": platform.platform(),
        "Architecture": platform.machine(),
        "Executable": sys.executable,
    }

    # Detect active Linux libc version if available
    try:
        import ctypes

        libc = ctypes.CDLL("libc.so.6")
        gnu_get_libc_version = libc.gnu_get_libc_version
        gnu_get_libc_version.restype = ctypes.c_char_p
        info["Host glibc"] = gnu_get_libc_version().decode("utf-8")
    except Exception:
        info["Host glibc"] = "Unknown"

    info["Desktop Session"] = os.environ.get("XDG_CURRENT_DESKTOP", "Unknown")
    info["Session Type"] = os.environ.get("XDG_SESSION_TYPE", "Unknown")
    return info


def print_startup_error(error: BaseException, context: str = "Startup") -> None:
    """Print an informative, clean error banner to stderr with diagnostic info."""
    diag = get_system_diagnostic_info()
    sys.stderr.write("\n" + "=" * 76 + "\n")
    sys.stderr.write(f" [Markup Notes Diagnostic Error] Failed during {context}\n")
    sys.stderr.write("=" * 76 + "\n")
    sys.stderr.write(f"Error Type: {type(error).__name__}\n")
    sys.stderr.write(f"Details:    {error}\n\n")
    sys.stderr.write("System Environment Diagnostics:\n")
    for key, val in diag.items():
        sys.stderr.write(f"  - {key}: {val}\n")
    sys.stderr.write("\nTroubleshooting:\n")
    sys.stderr.write(
        "  If this is an ImportError relating to dynamic libraries or Qt plugins,\n"
        "  ensure your Linux desktop packages (GLib, X11, Wayland) are installed:\n"
        "    Ubuntu / Debian / Pop!_OS: sudo apt install libglib2.0-0 libx11-6 libxcb1\n"
        "    Fedora / RHEL:             sudo dnf install glib2 libX11 libxcb\n"
        "    Arch / Manjaro / CachyOS:  sudo pacman -S glib2 libx11 libxcb\n"
    )
    sys.stderr.write("=" * 76 + "\n\n")
