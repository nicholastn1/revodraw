"""iPhone backend: drives the macOS "iPhone Mirroring" window instead of ADB.

Coordinates everywhere else in RevoDraw are screenshot pixels; here we map them
to screen points using the window bounds, then synthesize mouse drags.
Requires: Accessibility + Screen Recording permission for your terminal app.
"""
import subprocess
import time

import Quartz
from PIL import Image

APP_NAME = "iPhone Mirroring"
DRAG_STEPS = 8  # mouse-dragged events per segment; raise if lines come out dotted
TOUCH_HOLD = 0.08  # seconds to rest after touch-down before moving; raise if stroke starts get cut

_last = {}  # window bounds + image size from the latest screenshot


def _window():
    wins = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID)
    for w in wins:
        # the app also owns unnamed helper windows (menu bar strips); the phone window is titled
        if w.get('kCGWindowOwnerName') == APP_NAME and w.get('kCGWindowName') == APP_NAME:
            return w
    raise RuntimeError(f"'{APP_NAME}' window not found. Open the iPhone Mirroring app first.")


def activate():
    subprocess.run(['open', '-a', APP_NAME])
    time.sleep(0.5)
    if 'bounds' in _last:  # window may have moved since the screenshot
        _last['bounds'] = dict(_window()['kCGWindowBounds'])


def capture_screenshot(output_path: str = "screen.png") -> str:
    activate()
    w = _window()
    subprocess.run(['screencapture', '-x', '-o', '-l', str(w['kCGWindowNumber']), output_path], check=True)
    _last['bounds'] = dict(w['kCGWindowBounds'])
    _last['size'] = Image.open(output_path).size
    print(f"Screenshot saved to {output_path} ({_last['size'][0]}x{_last['size'][1]})")
    return output_path


def _to_screen(x, y):
    if 'bounds' not in _last:  # screenshot loaded manually; measure the window now
        w = _window()
        _last['bounds'] = dict(w['kCGWindowBounds'])
        tmp = '/tmp/revodraw_probe.png'
        subprocess.run(['screencapture', '-x', '-o', '-l', str(w['kCGWindowNumber']), tmp], check=True)
        _last['size'] = Image.open(tmp).size
    b, (iw, ih) = _last['bounds'], _last['size']
    return b['X'] + x * b['Width'] / iw, b['Y'] + y * b['Height'] / ih


def _post(kind, x, y):
    ev = Quartz.CGEventCreateMouseEvent(None, kind, (x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)


def draw_path(points, segment_ms=60):
    """One continuous touch through all points. iOS drops the start of short
    separate swipes (touch slop), so unlike ADB we never lift mid-path."""
    pts = [_to_screen(x, y) for x, y in points]
    dt = max(segment_ms, 1) / 1000 / DRAG_STEPS
    _post(Quartz.kCGEventLeftMouseDown, *pts[0])
    time.sleep(TOUCH_HOLD)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        for i in range(1, DRAG_STEPS + 1):
            t = i / DRAG_STEPS
            _post(Quartz.kCGEventLeftMouseDragged, ax + (bx - ax) * t, ay + (by - ay) * t)
            time.sleep(dt)
    _post(Quartz.kCGEventLeftMouseUp, *pts[-1])


def swipe(x1, y1, x2, y2, duration_ms):
    """Same contract as `adb shell input swipe` (also works as a tap)."""
    draw_path([(x1, y1), (x2, y2)], duration_ms)


if __name__ == '__main__':
    # Self-check of the coordinate mapping (no window needed).
    _last['bounds'] = {'X': 100, 'Y': 50, 'Width': 300, 'Height': 650}
    _last['size'] = (600, 1300)
    assert _to_screen(0, 0) == (100, 50)
    assert _to_screen(600, 1300) == (400, 700)
    assert _to_screen(300, 650) == (250, 375)
    print("mapping ok")
