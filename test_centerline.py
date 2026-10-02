"""Run: python test_centerline.py — centerline must draw a thick line once, not its outline."""
import cv2
import numpy as np
from revodraw import extract_centerline

img = np.full((60, 200), 255, np.uint8)
cv2.line(img, (20, 30), (180, 30), 0, 9)          # one thick horizontal stroke
paths = extract_centerline(img, 127, 1.0)
assert len(paths) == 1, paths                     # contours would give a closed outline (2 long edges)
xs = [p[0] for p in paths[0]]; ys = [p[1] for p in paths[0]]
assert max(xs) - min(xs) > 140 and max(ys) - min(ys) <= 2, paths   # straight, along the middle
assert all(abs(y - 30) <= 1 for y in ys)

img = np.full((100, 100), 255, np.uint8)
cv2.circle(img, (50, 50), 30, 0, 7)               # closed ring -> single loop path
assert len(extract_centerline(img, 127, 1.0)) == 1
print("centerline ok")

img = np.full((60, 60), 255, np.uint8)
cv2.circle(img, (30, 30), 4, 0, -1)               # solid dot (an eye) must survive as a tap
paths = extract_centerline(img, 127, 1.0)
assert len(paths) == 1 and all(abs(x - 30) <= 2 and abs(y - 30) <= 2 for x, y in paths[0]), paths
print("dot ok")

img = np.full((120, 120), 255, np.uint8)
cv2.line(img, (10, 10), (110, 100), 0, 7)         # diagonal + branch: no residue fragments
cv2.line(img, (60, 55), (20, 110), 0, 7)
paths = extract_centerline(img, 127, 1.0)
assert len(paths) <= 3 and all(len(p) >= 2 for p in paths), paths
print("no residue ok")
