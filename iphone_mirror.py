"""iPhone backend: drives the macOS "iPhone Mirroring" window instead of ADB.

Coordinates everywhere else in RevoDraw are screenshot pixels; here we map them
to screen points using the window bounds, then synthesize mouse drags.
Requires: Accessibility + Screen Recording permission for your terminal app.
"""
import math
import subprocess
import time

import Quartz
from PIL import Image

APP_NAME = "iPhone Mirroring"
TOUCH_HOLD = 0.08  # seconds to rest after touch-down before moving
STEP_PX = 2.0      # screen points per drag event
EVENT_DT = 0.02    # seconds between drag events; lower = faster but Mirroring starts dropping strokes
END_HOLD = 0.05    # rest before lift-off so the stroke's end registers
DOT_R = 1.5        # radius of the micro-circle that draws a dot
PREROLL_EVENTS = 4 # jiggle events at stroke start to absorb iOS drag-recognition latency
PREROLL_AMP = 1.0  # jiggle distance (pt), forward along the stroke and back, so it stays on the line

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


def _drag(pts):
    """Constant-speed touch through screen points. Calibrated on a real iPhone:
    - Mirroring drops movement sent faster than ~one event per 20ms (strokes short/missing)
    - iOS discards the first ~40ms of movement while it recognizes the drag, so strokes
      under ~8pt vanished and dots came out as half circles: a 1pt jiggle along the
      stroke direction eats that window without drawing anything visible
    - the end needs a beat before lift-off or the last bit is lost"""
    (ax, ay), (bx, by) = pts[0], next((p for p in pts if p != pts[0]), (pts[0][0] + 1, pts[0][1]))
    d = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / d, (by - ay) / d
    _post(Quartz.kCGEventLeftMouseDown, ax, ay)
    time.sleep(TOUCH_HOLD)
    for i in range(PREROLL_EVENTS):
        k = PREROLL_AMP if i % 2 == 0 else 0.0
        _post(Quartz.kCGEventLeftMouseDragged, ax + ux * k, ay + uy * k)
        time.sleep(EVENT_DT)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        steps = max(1, math.ceil(math.hypot(bx - ax, by - ay) / STEP_PX))
        for i in range(1, steps + 1):
            t = i / steps
            _post(Quartz.kCGEventLeftMouseDragged, ax + (bx - ax) * t, ay + (by - ay) * t)
            time.sleep(EVENT_DT)
    time.sleep(END_HOLD)
    _post(Quartz.kCGEventLeftMouseUp, *pts[-1])


def draw_path(points, segment_ms=None):
    """One continuous touch through all points (never lifts mid-path, unlike ADB swipes).
    segment_ms is ignored: speed is fixed by STEP_PX/EVENT_DT, which is what iOS needs."""
    pts = [_to_screen(x, y) for x, y in points]
    if all(p == pts[0] for p in pts):  # a dot: a stationary tap draws nothing, a tiny circle does
        cx, cy = pts[0]
        pts = [(cx + DOT_R * math.cos(a * math.pi / 3), cy + DOT_R * math.sin(a * math.pi / 3)) for a in range(7)]
    _drag(pts)


def swipe(x1, y1, x2, y2, duration_ms):
    """Same contract as `adb shell input swipe`; equal points are a plain tap (UI buttons)."""
    if (x1, y1) == (x2, y2):
        sx, sy = _to_screen(x1, y1)
        _post(Quartz.kCGEventLeftMouseDown, sx, sy)
        time.sleep(max(duration_ms, 30) / 1000)
        _post(Quartz.kCGEventLeftMouseUp, sx, sy)
    else:
        _drag([_to_screen(x1, y1), _to_screen(x2, y2)])


if __name__ == '__main__':
    # Self-check of the coordinate mapping (no window needed).
    _last['bounds'] = {'X': 100, 'Y': 50, 'Width': 300, 'Height': 650}
    _last['size'] = (600, 1300)
    assert _to_screen(0, 0) == (100, 50)
    assert _to_screen(600, 1300) == (400, 700)
    assert _to_screen(300, 650) == (250, 375)
    print("mapping ok")
