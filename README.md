# RevoDraw

Draw custom images on your Revolut card using your phone's drawing screen. RevoDraw automatically detects the drawing boundaries and lets you upload, edit, and draw images via ADB.

![RevoDraw Demo](https://img.shields.io/badge/Platform-Android-green) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

## Demo

![RevoDraw Demo](demo.gif)

## Features

- **Automatic boundary detection** - Detects the dotted-line drawing area from your phone screen
- **Manual screenshot loading** - Load a screenshot manually if ADB capture doesn't work
- **Multiple image layers** - Add multiple images and position them independently
- **Edge detection** - Multiple algorithms (auto, edges, contours, adaptive) to extract drawable paths
- **Real-time preview** - See exactly what will be drawn before executing
- **Transform controls** - Scale, rotate, flip, and position your images
- **Eraser tool** - Remove unwanted paths with precision
- **Reprocess** - Adjust edge detection settings and reprocess without re-uploading

## Requirements

- Python 3.8+
- Android phone with USB debugging enabled
- ADB (Android Debug Bridge) installed
- USB cable

**Optional:** [scrcpy](https://github.com/Genymobile/scrcpy) if you want to mirror your phone screen on your computer while drawing (not required - you can just watch your phone directly).

### For Xiaomi/Redmi devices
You must enable **"USB debugging (Security settings)"** in Developer Options, then reboot. This allows ADB to simulate touch input.

## Installation

```bash
# Clone the repository
git clone https://github.com/K53N0/revodraw.git
cd revodraw

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Web UI (Recommended)

```bash
python revodraw.py
```

Then open http://localhost:5000 in your browser.

**Steps:**
1. Connect your Android phone via USB
2. Open Revolut app → Cards → Design card → Freeform drawing
3. **Select the pen tool and set it to the smallest size** for optimal results
4. Click "Detect Area" to capture the drawing boundaries (or "Load Screenshot" to use a manual screenshot)
5. Upload an image and adjust edge detection settings
6. Position and transform your image using the preview
7. Click "Start Drawing" to draw on your phone

> **Tip:** Using the smallest pen size gives the cleanest, most detailed results.

> **Warning:** Keep some margin from the detected boundaries - they're not always 100% accurate. If your image is placed too close to the edges, the drawing strokes may accidentally interact with UI elements in the Revolut app and disrupt the drawing process. If this happens, restart and use a slightly smaller scale or reposition the image away from the edges.

### CLI Tools

**Draw shapes:**
```bash
python revolut_draw.py --heart
python revolut_draw.py --star
python revolut_draw.py --text "HELLO"
python revolut_draw.py --demo
```

**Draw images:**
```bash
python image_draw.py logo.png
python image_draw.py photo.jpg --method edges
python image_draw.py drawing.png --preview  # Preview without drawing
```

## iPhone (macOS only)

No ADB on iOS, so iPhone mode drives the macOS **iPhone Mirroring** window instead: it screenshots the window and draws with synthesized mouse drags.

See also [parkerxhollis/revo-draw-ios](https://github.com/parkerxhollis/revo-draw-ios), an earlier standalone project using the same iPhone Mirroring technique, with raster fill (pixel/row) drawing from a color-coded PNG template. This mode instead keeps RevoDraw's vector line tracing and web UI.

1. Open the **iPhone Mirroring** app (macOS 15+) until your iPhone screen shows up.
2. Give your terminal **Accessibility** and **Screen Recording** permission (System Settings → Privacy & Security).
3. Open Revolut → customise card → Draw, then run:

```bash
REVODRAW_IPHONE=1 python revodraw.py -p 5050   # port 5000 is taken by AirPlay on macOS
```

Notes:
- Don't touch the mouse while it draws (it uses the real cursor).
- The iOS drawing area is found from the faint dotted boundary (tiny specks, read off row/column histograms). Works for both card layouts seen so far (logo notch, or whole top band excluded).
- Knobs in `iphone_mirror.py` (calibrated with test patterns on a real iPhone): `EVENT_DT`/`STEP_PX` set the drag speed (faster drops strokes), `PREROLL_EVENTS` absorbs iOS drag-recognition latency (fewer = short strokes and dots vanish), `DOT_R` is the micro-circle used for dots (a stationary tap draws nothing).
- Brush thickness is Revolut's own slider (right side of the card), not RevoDraw's.
- For line art use **Centerline**: it draws each line once along its middle. *Contours* traces both edges of every thick line, which the brush merges into blobs.

## How It Works

1. **Screenshot capture** - Takes a screenshot via ADB (or loads a manually provided screenshot)
2. **Boundary detection** - Uses OpenCV to find the dotted-line drawing area
3. **Edge extraction** - Converts your image to drawable paths using edge detection
4. **Path scaling** - Fits paths within the detected boundaries
5. **ADB drawing** - Sends swipe commands to draw each path segment

## Configuration

### Edge Detection Methods

| Method | Best For |
|--------|----------|
| `auto` | Automatic selection based on image |
| `edges` | Photos, complex images |
| `contours` | Logos, drawings (dark on light) |
| `contours_inv` | Light on dark images |
| `adaptive` | Images with varying lighting |

### Parameters

- **Threshold** (0-255): Controls contour detection sensitivity
- **Simplify** (0-10): Higher values = fewer points, faster drawing

## Generating Images with AI

For best results, use images with clean lines and high contrast. You can use AI image generators to create custom artwork that's optimized for RevoDraw.

### Prompt Template

Use this prompt with your preferred AI image generator:

```
Create a minimalist line art illustration filling the entire canvas.

Requirements:
- Black lines on white background (or white on black)
- Clean, bold outlines with no gradients or shading
- No fill colors, only strokes/outlines
- High contrast, vector-style artwork
- Consistent line thickness
- Simple but striking design - avoid small intricate details

Theme: [YOUR THEME - e.g., "cyberpunk skull", "geometric wolf", "coding/hacker aesthetic"]

Style: Technical blueprint / line drawing / single-color stencil art

Important: The design must work as a simple outline that could be traced.
Avoid halftones, dots, textures, or soft edges.
```

### Using with Multimodal AI (Recommended)

For best results, provide the AI with a screenshot of your detected drawing area:

1. Click "Detect Area" in RevoDraw
2. Take a screenshot of the preview showing the L-shaped drawing boundary
3. Send the screenshot to a multimodal AI with this prompt:

```
I want to draw a custom image on my Revolut card using an automated tool.
The attached screenshot shows the available drawing area (the L-shaped region
with two exclusion zones in the corners).

Generate an image that:
- Fits within this L-shaped boundary
- Uses only black lines on white background
- Has clean, bold outlines (no gradients, shading, or fills)
- Is simple enough to be drawn with continuous strokes
- Theme: [YOUR THEME]

The image will be converted to paths using edge detection, so clean lines are essential.
```

### Tips for AI-Generated Images
- Request "line art", "stencil", or "vector style"
- Avoid: gradients, shading, photorealistic styles, fine details
- Best styles: tribal art, geometric patterns, minimalist logos, blueprint drawings
- If the result has too many details, ask the AI to "simplify" or make it "bolder"

## Troubleshooting

**"No ADB device connected"**
- Ensure USB debugging is enabled
- Check `adb devices` shows your phone
- Try different USB cable/port

**Drawing doesn't appear on phone**
- For Xiaomi: Enable "USB debugging (Security settings)" and reboot
- Make sure you're on the freeform drawing screen
- Try running `adb shell input tap 500 500` to test

**"Could not load image: screen.png"**
- The ADB screenshot may have produced corrupted data; RevoDraw will automatically retry with a fallback method
- If it still fails, use "Load Screenshot" to manually load a screenshot taken on your phone (transfer it to your computer first)

**Boundary detection fails**
- Ensure the card drawing screen is fully visible
- Avoid screen overlays or notifications
- Try adjusting screen brightness

## Project Structure

```
revodraw/
├── revodraw.py            # Main web UI
├── detect_drawing_area.py # Boundary detection module
├── revolut_draw.py        # CLI for shapes/text
├── image_draw.py          # CLI for images
└── requirements.txt       # Python dependencies
```

## License

MIT License - feel free to use and modify.

## Contributing

Contributions welcome! Please open an issue or PR.

## Disclaimer

This tool is for personal use. Use responsibly and in accordance with Revolut's terms of service.
