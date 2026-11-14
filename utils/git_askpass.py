#!/usr/bin/env python3
"""Transient Git credential askpass helper for in-memory HTTPS authentication."""

from __future__ import annotations

import os
import sys


def main() -> None:
    prompt = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    if "username" in prompt:
        # GitHub accepts username 'oauth2' or 'x-access-token' for personal access tokens
        sys.stdout.write(os.environ.get("MARKUP_NOTES_GIT_USER", "oauth2") + "\n")
    else:
        # Password prompt
        sys.stdout.write(os.environ.get("MARKUP_NOTES_GIT_TOKEN", "") + "\n")


if __name__ == "__main__":
    main()
