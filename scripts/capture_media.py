"""Regenerate every screenshot and the demo recording from the running app.

A screenshot nobody can regenerate starts lying quietly after the next UI change,
so the README's visuals are produced by this script rather than captured by hand.

    uv run --extra media python scripts/capture_media.py
    uv run --extra media python scripts/capture_media.py --only video
    uv run --extra media python scripts/capture_media.py --only video --seconds 30

Needs a RasterScope instance serving the built frontend (``make run``) and, for
the GIF and MP4, ``ffmpeg`` on PATH.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Page, Playwright, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "docs" / "images"
MEDIA_DIR = ROOT / "docs" / "media"

DESKTOP = {"width": 1440, "height": 900}
TALL = {"width": 1440, "height": 1180}
PHONE = {"width": 390, "height": 844}
VIDEO = {"width": 1440, "height": 960}

GIF_WIDTH = 860
GIF_FPS = 10
GIF_COLORS = 128
GIF_BUDGET_BYTES = 5_000_000
DEMO_SECONDS = 20


@dataclass(frozen=True)
class Options:
    base_url: str
    only: str
    seconds: int
    gif_width: int
    gif_fps: int


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def open_app(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.wait_for_selector(".comparison-frame")
    wait_for_imagery(page)
    page.wait_for_timeout(700)


def wait_for_imagery(page: Page) -> None:
    """A scenario is six separate PNGs; a recording must not start mid-decode."""
    page.wait_for_function("Array.from(document.images).every((image) => image.complete)")


def set_opacity(page: Page, value: str) -> None:
    # A range input only accepts a value that lands exactly on its step grid,
    # and only in the shortest spelling of it — "0.8", never "0.80".
    page.locator(".opacity-control input").fill(value)


def pick_layer(page: Page, label: str) -> None:
    page.get_by_role("button", name=label, exact=True).click()
    page.wait_for_timeout(450)


def pick_surface(page: Page, label: str) -> None:
    page.locator(".nav-item", has_text=label).click()
    page.wait_for_timeout(700)


def frame_point(page: Page, x_ratio: float, y_ratio: float) -> tuple[float, float]:
    box = page.locator(".comparison-frame").bounding_box()
    assert box is not None, "the comparison frame is not laid out"
    return box["x"] + box["width"] * x_ratio, box["y"] + box["height"] * y_ratio


def drag_divider(page: Page, to_ratio: float, steps: int = 26, hold: int = 16) -> None:
    """Drag the divider handle the way a hand does: gradually, with frames in between."""
    handle = page.locator(".comparison-handle").bounding_box()
    assert handle is not None
    start_x = handle["x"] + handle["width"] / 2
    start_y = handle["y"] + handle["height"] / 2
    end_x, _ = frame_point(page, to_ratio, 0.5)
    page.mouse.move(start_x, start_y)
    page.mouse.down()
    for step in range(1, steps + 1):
        page.mouse.move(start_x + (end_x - start_x) * step / steps, start_y)
        page.wait_for_timeout(hold)
    page.mouse.up()


# --------------------------------------------------------------------------- #
# screenshots
# --------------------------------------------------------------------------- #


def capture_screenshots(pw: Playwright, options: Options) -> list[Path]:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    browser = pw.chromium.launch()

    def shot(page: Page, name: str) -> None:
        # Frames dominated by satellite imagery are photographs and weigh three
        # times as much as PNG; frames of type and rules stay lossless.
        target = IMAGE_DIR / name
        if target.suffix == ".jpg":
            page.screenshot(path=target, type="jpeg", quality=94)
        else:
            page.screenshot(path=target)
        written.append(target)

    # 1 · the default workbench, and 2 · a pixel inspected under the class overlay
    context = browser.new_context(
        viewport=DESKTOP, device_scale_factor=2, color_scheme="light", reduced_motion="reduce"
    )
    page = context.new_page()
    open_app(page, options.base_url)
    shot(page, "rasterscope-compare-desktop.jpg")

    pick_layer(page, "Classes")
    page.mouse.click(*frame_point(page, 0.3, 0.42))
    page.wait_for_selector(".pixel-readout")
    page.wait_for_timeout(400)
    shot(page, "rasterscope-classes-inspect.jpg")

    pick_layer(page, "Uncertainty")
    # The entropy ramp already fades itself by alpha; at the default 56 % the
    # layer is too faint to read in a static image.
    set_opacity(page, "0.85")
    page.wait_for_timeout(600)
    shot(page, "rasterscope-uncertainty.jpg")

    # 3 · the out-of-distribution scenario, with its warning
    page.select_option("#scenario", "brazil-domain-shift")
    wait_for_imagery(page)
    pick_layer(page, "Classes")
    page.wait_for_timeout(700)
    shot(page, "rasterscope-domain-shift.jpg")
    context.close()

    # 4 · model evidence, which needs a taller viewport to read as one page
    context = browser.new_context(
        viewport=TALL, device_scale_factor=2, color_scheme="light", reduced_motion="reduce"
    )
    page = context.new_page()
    open_app(page, options.base_url)
    pick_surface(page, "Model lab")
    shot(page, "rasterscope-model-lab.png")
    context.close()

    # 5 · the same instrument in the dark scheme
    context = browser.new_context(
        viewport=DESKTOP, device_scale_factor=2, color_scheme="dark", reduced_motion="reduce"
    )
    page = context.new_page()
    open_app(page, options.base_url)
    pick_layer(page, "Classes")
    shot(page, "rasterscope-compare-dark.jpg")
    context.close()

    # 6 · a phone, where every control has to remain reachable
    context = browser.new_context(
        viewport=PHONE,
        device_scale_factor=3,
        color_scheme="light",
        is_mobile=True,
        has_touch=True,
        reduced_motion="reduce",
    )
    page = context.new_page()
    open_app(page, options.base_url)
    pick_layer(page, "Classes")
    shot(page, "rasterscope-compare-mobile.jpg")
    context.close()

    browser.close()
    return written


# --------------------------------------------------------------------------- #
# recording
# --------------------------------------------------------------------------- #


def demo_20s(page: Page) -> None:
    """Twenty seconds: every surface, no room to linger."""
    page.wait_for_timeout(900)  # 0.0  the workbench, at rest
    drag_divider(page, 0.80)  # 1.0  compare the two dates
    page.wait_for_timeout(250)
    drag_divider(page, 0.24)
    page.wait_for_timeout(350)
    drag_divider(page, 0.52, steps=14)

    pick_layer(page, "Classes")  # 5.0  predicted land cover
    page.wait_for_timeout(500)
    drag_divider(page, 0.78, steps=20)
    page.wait_for_timeout(300)

    for value in ("0.75", "0.35", "0.55"):  # 7.5  the overlay is adjustable
        set_opacity(page, value)
        page.wait_for_timeout(420)

    page.mouse.click(*frame_point(page, 0.34, 0.45))  # 9.0  inspect one pixel
    page.wait_for_selector(".pixel-readout")
    page.wait_for_timeout(1700)

    pick_layer(page, "Uncertainty")  # 11.0 where the model hesitates
    set_opacity(page, "0.85")
    page.wait_for_timeout(1500)
    drag_divider(page, 0.40, steps=16)

    page.select_option("#scenario", "brazil-domain-shift")  # 13.5 the stated blind spot
    wait_for_imagery(page)
    pick_layer(page, "Classes")
    page.wait_for_timeout(1900)

    pick_surface(page, "Model lab")  # 16.0 held-out evidence
    page.wait_for_timeout(1600)
    page.mouse.wheel(0, 340)
    page.wait_for_timeout(2600)  # 20.0 rest on the failing classes


def demo_30s(page: Page) -> None:
    """Thirty seconds: the same order, paced so each step can be read."""
    page.wait_for_timeout(1300)  # 0.0  the workbench, at rest
    drag_divider(page, 0.82, steps=30, hold=20)  # 1.3  compare the two dates
    page.wait_for_timeout(600)
    drag_divider(page, 0.20, steps=32, hold=20)
    page.wait_for_timeout(600)
    drag_divider(page, 0.52, steps=18, hold=18)
    page.wait_for_timeout(500)

    pick_layer(page, "Classes")  # 6.5  predicted land cover
    page.wait_for_timeout(1100)
    drag_divider(page, 0.80, steps=26, hold=20)
    page.wait_for_timeout(700)

    for value in ("0.8", "0.3", "0.55"):  # 10.5 the overlay is adjustable
        set_opacity(page, value)
        page.wait_for_timeout(620)

    page.mouse.click(*frame_point(page, 0.34, 0.45))  # 13.0 inspect one pixel
    page.wait_for_selector(".pixel-readout")
    page.wait_for_timeout(2600)

    pick_layer(page, "Uncertainty")  # 16.0 where the model hesitates
    set_opacity(page, "0.85")
    page.wait_for_timeout(2300)
    drag_divider(page, 0.38, steps=24, hold=20)
    page.wait_for_timeout(900)

    page.select_option("#scenario", "brazil-domain-shift")  # 20.0 the stated blind spot
    wait_for_imagery(page)
    pick_layer(page, "Classes")
    page.wait_for_timeout(1800)
    drag_divider(page, 0.74, steps=24, hold=20)
    page.wait_for_timeout(1500)

    pick_surface(page, "Model lab")  # 25.0 held-out evidence
    page.wait_for_timeout(2400)  # the baseline beside the runtime model
    page.mouse.wheel(0, 360)
    page.wait_for_timeout(3000)  # 30.0 rest on the two classes it never predicts


CHOREOGRAPHY = {20: demo_20s, 30: demo_30s}


def record_demo(pw: Playwright, options: Options) -> Path:
    """Drive the product once, on the clock, and keep the raw recording."""
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    raw_dir = MEDIA_DIR / "_raw"
    if raw_dir.exists():
        shutil.rmtree(raw_dir)

    browser = pw.chromium.launch()
    context = browser.new_context(
        viewport=VIDEO,
        color_scheme="light",
        record_video_dir=str(raw_dir),
        record_video_size=VIDEO,
    )
    page = context.new_page()
    open_app(page, options.base_url)
    CHOREOGRAPHY[options.seconds](page)
    context.close()
    browser.close()

    source = next(raw_dir.glob("*.webm"))
    webm = MEDIA_DIR / f"{stem(options)}.webm"
    shutil.move(str(source), webm)
    shutil.rmtree(raw_dir, ignore_errors=True)
    return webm


def stem(options: Options) -> str:
    """The 20-second cut is the one the README embeds, so it keeps the plain name."""
    return "rasterscope-demo" if options.seconds == 20 else f"rasterscope-demo-{options.seconds}s"


def encode(webm: Path, options: Options) -> list[Path]:
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found on PATH; keeping the raw recording only.", file=sys.stderr)
        return [webm]

    trim = ["-t", str(options.seconds)]
    mp4 = MEDIA_DIR / f"{stem(options)}.mp4"
    run(
        [
            "-i",
            str(webm),
            *trim,
            "-vf",
            "scale=1440:-2:flags=lanczos,fps=30",
            "-c:v",
            "libx264",
            "-profile:v",
            "high",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "20",
            "-movflags",
            "+faststart",
            str(mp4),
        ]
    )

    gif = MEDIA_DIR / f"{stem(options)}.gif"
    width = options.gif_width
    # LinkedIn refuses an image over about 5 MB, and a longer cut of photographic
    # frames does not fit at the same width, so the width gives way rather than
    # the duration. Four attempts is enough to cross the budget from any start.
    for attempt in range(4):
        write_gif(webm, gif, trim, width, options.gif_fps)
        if gif.stat().st_size <= GIF_BUDGET_BYTES or attempt == 3:
            break
        width = round(width * 0.88)
    if width != options.gif_width:
        print(f"GIF narrowed to {width}px to fit the {GIF_BUDGET_BYTES / 1_000_000:.0f} MB budget.")

    return [mp4, gif, webm]


def write_gif(webm: Path, gif: Path, trim: list[str], width: int, fps: int) -> None:
    """Two passes: photographic frames need a palette built from the whole clip,
    otherwise the greens band badly. Bayer dithering rather than an error-diffusion
    kernel because it costs roughly a third of the bytes on this footage."""
    palette = MEDIA_DIR / "_palette.png"
    scale = f"fps={fps},scale={width}:-1:flags=lanczos"
    run(
        [
            "-i",
            str(webm),
            *trim,
            "-vf",
            f"{scale},palettegen=max_colors={GIF_COLORS}:stats_mode=diff",
            str(palette),
        ]
    )
    run(
        [
            "-i",
            str(webm),
            "-i",
            str(palette),
            *trim,
            "-lavfi",
            f"{scale}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
            "-loop",
            "0",
            str(gif),
        ]
    )
    palette.unlink(missing_ok=True)


def run(arguments: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", *arguments], check=True, capture_output=True)


# --------------------------------------------------------------------------- #


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--only", choices=["all", "screenshots", "video"], default="all")
    parser.add_argument("--seconds", type=int, choices=sorted(CHOREOGRAPHY), default=DEMO_SECONDS)
    parser.add_argument("--gif-width", type=int, default=GIF_WIDTH)
    parser.add_argument("--gif-fps", type=int, default=GIF_FPS)
    args = parser.parse_args()
    options = Options(
        args.base_url.rstrip("/"), args.only, args.seconds, args.gif_width, args.gif_fps
    )

    produced: list[Path] = []
    with sync_playwright() as pw:
        if options.only in {"all", "screenshots"}:
            produced += capture_screenshots(pw, options)
        if options.only in {"all", "video"}:
            produced += encode(record_demo(pw, options), options)

    for path in produced:
        size = path.stat().st_size / 1_000_000
        print(f"{path.relative_to(ROOT).as_posix():<46} {size:6.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
