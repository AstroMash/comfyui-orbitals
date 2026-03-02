"""Orbitals

Custom nodes for ComfyUI, created by AstroMash.
Occasional overkill. Zero apologies.
"""

from __future__ import annotations

import os
import sys


def _supports_color() -> bool:
    """Best-effort ANSI color support (safe when output is redirected)."""
    if os.environ.get("NO_COLOR"):
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


_COLOR = _supports_color()


def _c(text: str, code: str) -> str:
    if not _COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


_ANSI_RE = None


def _strip_ansi(s: str) -> str:
    global _ANSI_RE
    if _ANSI_RE is None:
        import re

        _ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
    return _ANSI_RE.sub("", s)


def _vw(s: str) -> int:
    """
    Visible width.

    We try to use wcwidth (if installed) for nicer emoji width handling,
    but we never draw left/right borders, so a len() fallback is fine.
    """
    plain = _strip_ansi(s)
    try:
        from wcwidth import wcswidth  # type: ignore

        w = wcswidth(plain)
        return w if w >= 0 else len(plain)
    except Exception:
        return len(plain)


def _pad(s: str, width: int) -> str:
    return s + (" " * max(0, width - _vw(s)))


def _banner(lines: list[str], rail_code: str = "38;5;39") -> None:
    """
    Top/bottom border only. No left/right borders.
    """
    width = max((_vw(l) for l in lines), default=0)
    top = "┌" + "─" * (width + 2) + "┐"
    bot = "└" + "─" * (width + 2) + "┘"

    print()
    print(_c(top, rail_code))
    for l in lines:
        print("  " + _pad(l, width))
    print(_c(bot, rail_code))
    print()


def _node_line(name_with_emoji: str, ok: bool, error: str | None = None) -> str:
    status = _c("✅", "38;5;82") if ok else _c("⚠", "38;5;214")
    base = _pad(name_with_emoji, 30) + " " + status
    if error:
        return base + " " + _c(error, "38;5;214")
    return base


NODE_CLASS_MAPPINGS: dict = {}
NODE_DISPLAY_NAME_MAPPINGS: dict = {}

_loaded: list[str] = []
_failed: list[tuple[str, str]] = []  # (label, error)


try:
    from .taggregator import NODE_CLASS_MAPPINGS as TAGGREGATOR_MAPPINGS
    from .taggregator import NODE_DISPLAY_NAME_MAPPINGS as TAGGREGATOR_DISPLAY_MAPPINGS

    NODE_CLASS_MAPPINGS.update(TAGGREGATOR_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(TAGGREGATOR_DISPLAY_MAPPINGS)
    _loaded.append("🏷️ Taggregator")
except ImportError as e:
    _failed.append(("🏷️ Taggregator", str(e)))


try:
    from .clip_encode_from_string import NODE_CLASS_MAPPINGS as CLIP_MAPPINGS
    from .clip_encode_from_string import NODE_DISPLAY_NAME_MAPPINGS as CLIP_DISPLAY_MAPPINGS

    NODE_CLASS_MAPPINGS.update(CLIP_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(CLIP_DISPLAY_MAPPINGS)
    _loaded.append("🔤 CLIP Encode (From String)")
except ImportError as e:
    _failed.append(("🔤 CLIP Encode (From String)", str(e)))


try:
    from .latent_gc import NODE_CLASS_MAPPINGS as LATENT_GC_MAPPINGS
    from .latent_gc import NODE_DISPLAY_NAME_MAPPINGS as LATENT_GC_DISPLAY_MAPPINGS

    NODE_CLASS_MAPPINGS.update(LATENT_GC_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(LATENT_GC_DISPLAY_MAPPINGS)
    _loaded.append("🗑️ Latent Garbage Collector")
except ImportError as e:
    _failed.append(("🗑️ Latent Garbage Collector", str(e)))


try:
    from .indexed_selector import NODE_CLASS_MAPPINGS as SELECTOR_MAPPINGS
    from .indexed_selector import NODE_DISPLAY_NAME_MAPPINGS as SELECTOR_DISPLAY_MAPPINGS

    NODE_CLASS_MAPPINGS.update(SELECTOR_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(SELECTOR_DISPLAY_MAPPINGS)
    _loaded.append("🎯 Select (Index)")
except ImportError as e:
    _failed.append(("🎯 Select (Index)", str(e)))


WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]


loaded_count = len(NODE_CLASS_MAPPINGS)
failed_count = len(_failed)

lines: list[str] = [
    _c("💫 Orbitals", "1;38;5;213"),
    _c("Ready", "38;5;82")
    + "  "
    + _c(f"{loaded_count} node(s)", "1;38;5;255")
    + ("" if failed_count == 0 else "  " + _c(f"⚠ {failed_count} missing", "38;5;214")),
    "",
    _c("Nodes", "38;5;250"),
]

for n in _loaded:
    lines.append(_node_line(n, ok=True))

for (label, err) in _failed:
    lines.append(_node_line(label, ok=False, error=err))

_banner(lines)