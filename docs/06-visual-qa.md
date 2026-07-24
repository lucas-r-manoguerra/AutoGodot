# Visual QA System

This document explains the screen capture pipeline, how visual QA works, and how AI agents can use screenshots to evaluate game design.

## Overview

The Visual QA system captures screenshots of the running Godot game and returns them as Base64-encoded JPEG images that AI agents can process to evaluate visual design, layout, and composition.

```
┌──────────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│ Running Game     │────>│ mss capture  │────>│ Pillow       │────>│ Base64      │
│ (Godot window)   │     │ (XComposite) │     │ resize+JPEG  │     │ encode      │
└──────────────────┘     └──────────────┘     └──────────────┘     └──────┬──────┘
                                                                          │
                                                                          ▼
                                                                ┌─────────────────┐
                                                                │ MCP Response    │
                                                                │ (JSON string    │
                                                                │  with Base64)   │
                                                                └─────────────────┘
```

## Capture Pipeline

### Step 1: Screen Capture (mss)

```python
with mss.mss() as sct:
    monitor = sct.monitors[1]  # Primary monitor
    screenshot = sct.grab(monitor)
```

**How mss works on Linux:**
- Uses XComposite extension (part of X11)
- No special permissions required
- Captures the full monitor at native resolution
- Returns raw RGB pixels

**Limitations:**
- Captures the full monitor, not a specific window
- If the game is in windowed mode, other desktop elements will be visible
- Wayland support is experimental (X11 recommended)

**Best practice:** Run the game in fullscreen or maximize the game window before capturing.

### Step 2: Image Processing (Pillow)

```python
# Convert raw capture to PIL Image
img = Image.open(io.BytesIO(raw_png))

# Resize preserving aspect ratio
ratio = min(max_width / original_width, max_height / original_height)
if ratio < 1.0:
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

# Encode to JPEG
img.convert("RGB").save(buffer, format="JPEG", quality=quality, optimize=True)
```

**Resize behavior:**
- Aspect ratio is always preserved
- Images smaller than the bounds are NOT upscaled (ratio stays ≥ 1.0)
- Images larger than the bounds are downscaled to fit
- LANCZOS resampling provides high-quality downscaling

**JPEG encoding:**
- Quality is configurable (10-100, default 85)
- `optimize=True` reduces file size with minimal quality loss
- RGB mode strips alpha channel (JPEG doesn't support transparency)

### Step 3: Base64 Encoding

```python
b64_string = base64.b64encode(jpeg_bytes).decode("ascii")
```

The JPEG bytes are Base64-encoded so they can be included in the MCP JSON response as a string field.

## Using Visual QA

### Typical Workflow

```
1. AI agent writes game code:
   write_game_file("scripts/player.gd", "...")

2. AI agent launches the game:
   run_godot_test("scenes/game.tscn", timeout=30)

3. AI agent captures a screenshot:
   capture_game_screen(1280, 720, quality=85)

4. AI agent processes the Base64 image to evaluate:
   - Scene composition and layout
   - UI element positioning
   - Sprite placement and scaling
   - Color palette and visual consistency
   - Error states (missing textures, broken layouts)

5. If issues found, AI agent modifies code and repeats from step 1
```

### What AI Agents Can Evaluate

**Layout and Composition:**
- Are UI elements properly positioned?
- Is there sufficient spacing between elements?
- Does the visual hierarchy guide the player's eye?
- Are elements overlapping unexpectedly?

**Sprite and Asset Quality:**
- Are sprites scaled correctly?
- Are textures loading (no pink/black placeholders)?
- Is the art style consistent across assets?
- Are animations playing correctly (check multiple captures)?

**UI Design:**
- Are buttons and interactive elements clearly visible?
- Is text readable at the target resolution?
- Do hover/active states look correct?
- Is the HUD information clear and unobtrusive?

**Error Detection:**
- Missing textures (bright pink/magenta squares)
- Broken layouts (elements outside screen bounds)
- Rendering artifacts (z-fighting, flickering)
- Incorrect colors (inverted, desaturated)

### Capture Settings Guide

| Scenario | Width | Height | Quality | Notes |
|----------|-------|--------|---------|-------|
| Quick check | 640 | 480 | 50 | Fast, low bandwidth |
| Standard QA | 1280 | 720 | 85 | Default, good balance |
| Detail inspection | 1920 | 1080 | 95 | High quality for fine details |
| Mobile preview | 390 | 844 | 80 | iPhone-like aspect ratio |

## Technical Details

### Why mss Over Alternatives?

| Library | Pros | Cons | Why We Chose mss |
|---------|------|------|-----------------|
| **mss** | Fast, cross-platform, no X11 config | Captures full monitor | Best balance of simplicity and performance |
| **python-xlib** | Direct X11 access | Complex setup, X11 only | Too much configuration required |
| **Pillow (ImageGrab)** | Simple API | Limited Linux support | Not reliable on all Linux setups |
| **scrot/maim CLI** | Simple | External dependency, slow | Adds process spawn overhead |
| **Qt screenshot** | Cross-platform | Requires Qt installation | Heavy dependency for a simple task |

### Why JPEG Over PNG?

| Format | Size | Quality | Transparency | Speed |
|--------|------|---------|:------------:|-------|
| **JPEG** | Small | Lossy | No | Fast encode |
| **PNG** | Large | Lossless | Yes | Slow encode |

For LLM consumption, JPEG is preferred because:
- Smaller Base64 strings (less context window usage)
- Faster encoding
- Transparency is not needed for screenshots
- Quality 85 is visually indistinguishable from lossless for most content

### Performance Characteristics

| Operation | Typical Time |
|-----------|-------------|
| mss capture | ~50-100ms |
| Pillow resize | ~20-50ms |
| JPEG encode | ~10-30ms |
| Base64 encode | ~5-10ms |
| **Total** | **~100-200ms** |

The entire capture pipeline completes in under 200ms on modern hardware.

## Limitations and Workarounds

### Limitation: Full Monitor Capture

**Problem:** `mss` captures the entire monitor, not just the game window.

**Workaround:** Run the game in fullscreen mode before capturing. Alternatively, position the game window to fill most of the screen.

**Future solution:** Window-specific capture using X11 window ID or Godot's built-in screenshot API (if exposed via CLI).

### Limitation: No Wayland Support

**Problem:** `mss` uses XComposite, which is X11-only.

**Workaround:** Use X11 session (most Ubuntu setups default to X11). For Wayland, `mss` has experimental support but it's not reliable.

**Future solution:** Use `grim` for Wayland capture, or implement a Godot-based capture using `get_viewport().get_texture().get_image()`.

### Limitation: No Runtime Game State

**Problem:** The screenshot shows pixels only. We can't inspect node positions, collision shapes, or game state.

**Workaround:** Use `run_godot_test` with debug output to get textual state information alongside screenshots.

**Future solution:** Runtime Probe pattern (like Godot-MCP-Native) for live game introspection.

## Visual QA Checklist

When evaluating a screenshot, check these items:

### Composition
- [ ] Main subject is clearly visible
- [ ] Rule of thirds / golden ratio applied
- [ ] No distracting background elements
- [ ] Depth cues (parallax, fog, scale) work correctly

### UI
- [ ] All text is readable at target resolution
- [ ] Buttons have sufficient touch/click targets
- [ ] HUD doesn't obstruct gameplay area
- [ ] Color contrast meets accessibility standards

### Art
- [ ] Consistent art style across all assets
- [ ] No missing textures (pink/black squares)
- [ ] Sprite scaling is appropriate
- [ ] Color palette is cohesive

### Technical
- [ ] No rendering artifacts
- [ ] No z-fighting (overlapping geometry flickering)
- [ ] Proper layer ordering (2D) / depth sorting (3D)
- [ ] Correct aspect ratio (no stretching/squishing)
