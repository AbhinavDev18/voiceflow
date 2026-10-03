import os
import subprocess


def paste_text(text: str):
    if not text:
        return False

    if os.environ.get("WAYLAND_DISPLAY"):
        result = subprocess.run(
            ["ydotool", "type", "--", text],
            check=False,
        )
        return result.returncode == 0

    result = subprocess.run(
        ["xdotool", "type", "--clearmodifiers", "--", text],
        check=False,
    )
    return result.returncode == 0
