"""Orbitals

Custom nodes for ComfyUI, created by AstroMash.
Occasional overkill. Zero apologies.
"""

from __future__ import annotations

NODE_CLASS_MAPPINGS: dict = {}
NODE_DISPLAY_NAME_MAPPINGS: dict = {}

_loaded: list[str] = []
_failed: list[tuple[str, str]] = []  # (label, error)


def _clean_label(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    # Strip leading emoji + space if present (common in Comfy node banners)
    if " " in s and not s[0].isalnum():
        return s.split(" ", 1)[1].strip()
    return s


def _pad(s: str, w: int) -> str:
    return s + (" " * max(0, w - len(s)))


def _center(s: str, w: int) -> str:
    if len(s) >= w:
        return s[:w]
    left = (w - len(s)) // 2
    right = w - len(s) - left
    return (" " * left) + s + (" " * right)


def _shadow(i: int) -> str:
    # return "░" if i % 2 == 0 else "▒"
    return "░" if i % 2 == 0 else "░"


def _triple_bar_row(panel_w: int, a: str, b: str, c: str) -> tuple[str, str, str]:
    inner = panel_w - 2  # excludes the two outer │

    a = a.strip()
    b = b.strip()
    c = c.strip()

    def want(s: str) -> int:
        return len(s) + 2  # space + content + space

    def cell(s: str, w: int) -> str:
        if w <= 2:
            return " " * w
        s = s[: (w - 2)]
        return " " + s + (" " * (w - 2 - len(s))) + " "

    # Minimums so labels don't look busted in normal terminals
    min_outer = 14  # enough for " Status: READY "
    min_mid = 12    # enough for " Loaded: 4 " etc.

    outer = max(min_outer, want(a), want(c))
    mid = max(min_mid, want(b))

    # First pass: give middle whatever remains after equal outers
    if 2 * outer + mid < inner:
        mid = inner - 2 * outer
    elif 2 * outer + mid > inner:
        over = (2 * outer + mid) - inner

        # 1) shrink middle first
        take = min(over, max(0, mid - min_mid))
        mid -= take
        over -= take

        # 2) shrink outer columns equally
        if over > 0:
            max_shrink_each = max(0, outer - min_outer)
            shrink_each = min(max_shrink_each, (over + 1) // 2)
            outer -= shrink_each
            over -= 2 * shrink_each

        # 3) if still over (tiny terminal), squeeze everyone while keeping outer equal
        while over > 0 and (outer > 3 or mid > 3):
            if mid > 3:
                mid -= 1
                over -= 1
                if over <= 0:
                    break
            if outer > 3:
                outer -= 1
                over -= 2
                if over <= 0:
                    break

    w1 = outer
    w2 = max(3, inner - 2 * w1)
    w3 = w1

    top_div = "├" + ("─" * w1) + "┬" + ("─" * w2) + "┬" + ("─" * w3) + "┤"
    row = "│" + cell(a, w1) + "│" + cell(b, w2) + "│" + cell(c, w3) + "│"
    bot_div = "├" + ("─" * w1) + "┴" + ("─" * w2) + "┴" + ("─" * w3) + "┤"

    return top_div, row, bot_div

def _render_panel(loaded: list[str], failed: list[tuple[str, str]]) -> None:
    loaded_clean = [_clean_label(x) for x in loaded]
    failed_clean = [(_clean_label(a), b) for (a, b) in failed]

    loaded_count = len(loaded_clean)
    failed_count = len(failed_clean)

    title = "O · R · B · I · T · A · L · S"
    # Inner framed box width (between ╔ ╗). Chosen to match your mock while staying dynamic.
    inner_box_w = max(39, len(title) + 10, max((len(n) for n in loaded_clean), default=0) + 12)
    inner_box_w = min(inner_box_w, 55)  # keep it sane in narrow consoles

    panel_w = inner_box_w + 6  # derived from your mock: outer padding around inner framed box
    outer_top = "╭" + ("─" * panel_w) + "╮"
    outer_bot = "╰" + ("─" * panel_w) + "╯"

    inner_top = "╔" + ("═" * inner_box_w) + "╗"
    inner_bot = "╚" + ("═" * inner_box_w) + "╝"

    lines: list[str] = []
    shadow_i = 0

    lines.append(outer_top)
    lines.append("│  " + inner_top + "  │" + _shadow(shadow_i)); shadow_i += 1

    title_line = _center(title, inner_box_w)
    # The fancy splice line with ├──╢ ... ╟──┤
    lines.append("├──╢" + title_line + "╟──┤" + _shadow(shadow_i)); shadow_i += 1

    lines.append("│  " + inner_bot + "  │" + _shadow(shadow_i)); shadow_i += 1

    a = " Status: READY " if failed_count == 0 else " Status: DEGRADED "
    b = f"  Loaded: {loaded_count}  "
    c = f"  Missing: {failed_count}   "
    div_top, stat_row, div_bot = _triple_bar_row(panel_w, a, b, c)

    lines.append(div_top + _shadow(shadow_i)); shadow_i += 1
    lines.append(stat_row + _shadow(shadow_i)); shadow_i += 1
    lines.append(div_bot + _shadow(shadow_i)); shadow_i += 1

    # Nodes box
    lines.append("│  " + inner_top + "  │" + _shadow(shadow_i)); shadow_i += 1

    nodes_title = "  Nodes"
    lines.append("│  " + "║" + _pad(nodes_title, inner_box_w) + "║" + "  │" + _shadow(shadow_i)); shadow_i += 1
    lines.append("│  " + "╟" + ("─" * inner_box_w) + "╢" + "  │" + _shadow(shadow_i)); shadow_i += 1

    status_tag_ok = "[ OK ]"
    status_tag_bad = "[ !! ]"
    name_w = max((len(n) for n in loaded_clean), default=0)
    name_w = max(name_w, 10)
    # Fit inside: "║  " + name + spaces + status + "  ║"
    # We'll compute available name padding dynamically.
    avail_for_name = inner_box_w - 2 - 2 - len(status_tag_ok)  # left "  ", two spaces before status, status
    name_w = min(name_w, max(10, avail_for_name))

    def node_row(name: str, ok: bool) -> str:
        tag = status_tag_ok if ok else status_tag_bad
        left = "  " + _pad(name, name_w)
        mid_spaces = max(2, inner_box_w - len(left) - len(tag) - 2)
        return "║" + left + (" " * mid_spaces) + tag + "  " + "║"

    for n in loaded_clean:
        lines.append("│  " + node_row(n, True) + "  │" + _shadow(shadow_i)); shadow_i += 1

    for (n, _) in failed_clean:
        lines.append("│  " + node_row(n, False) + "  │" + _shadow(shadow_i)); shadow_i += 1

    lines.append("│  " + inner_bot + "  │" + _shadow(shadow_i)); shadow_i += 1
    lines.append(outer_bot + _shadow(shadow_i)); shadow_i += 1
    lines.append(" " + ("░" * (panel_w + 2)))

    print()
    for l in lines:
        print(l)
    print()


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

_render_panel(_loaded, _failed)