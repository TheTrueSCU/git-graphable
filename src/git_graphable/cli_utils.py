from typing import Any, Dict, List


def parse_style_overrides(styles: List[str]) -> Dict[str, Any]:
    """Parse key:prop:val list into nested theme dict."""
    theme = {}
    for s in styles:
        parts = s.split(":", 2)
        if len(parts) == 3:
            key, prop, val = parts
            if key not in theme:
                theme[key] = {}
            # Try to convert to int if possible (for width)
            if val.isdigit():
                val = int(val)
            theme[key][prop] = val
    return theme
