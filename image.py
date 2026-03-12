from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
import time
import os
from waveshare_epd import epd10in2g

# ── Display dimensions ──────────────────────────────────────────────────────
WIDTH, HEIGHT = 960, 640

# ── Font path — update if your Pi has a different font available ────────────
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


# ── Image utilities ─────────────────────────────────────────────────────────

def prepare_image(path: str) -> Image.Image:
    """
    Load, resize, and convert an image to high-contrast B&W
    optimized for e-ink rendering.
    """
    img = Image.open(path).resize((WIDTH, HEIGHT), Image.LANCZOS)

    # Convert to grayscale first
    img = img.convert("L")

    # Boost contrast so sheet music lines are crisp
    img = ImageEnhance.Contrast(img).enhance(2.0)

    # Sharpen slightly to keep staff lines clean
    img = img.filter(ImageFilter.SHARPEN)

    # Convert to pure 1-bit B&W — dithering disabled for crisper music notation
    img = img.convert("1", dither=Image.Dither.NONE)

    # Driver expects "RGB" mode buffer
    return img.convert("RGB")


def make_text_screen(lines: str | list[str], font_size: int = 48) -> Image.Image:
    """
    Creates a B&W image with centered text, ready to buffer and display.
    Accepts either a plain string (supports \\n) or a list of lines.
    """
    # Normalize input to a list of lines
    if isinstance(lines, str):
        lines = lines.split("\n")

    img  = Image.new("RGB", (WIDTH, HEIGHT), color="white")
    draw = ImageDraw.Draw(img)

    # Try to load a nicer font, fall back to PIL default
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except OSError:
        print(f"Warning: font not found at {FONT_PATH}, using PIL default.")
        font = ImageFont.load_default()

    line_height  = font_size + 12       # padding between lines
    total_height = line_height * len(lines)
    y = (HEIGHT - total_height) // 2    # vertically center the block

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2   # horizontally center each line
        draw.text((x, y), line, fill="black", font=font)
        y += line_height

    return img


def load_images(image_dir: str = ".") -> list[Image.Image]:
    """Load all PNG/JPG images from a directory, sorted by filename."""
    extensions = (".png", ".jpg", ".jpeg")
    files = sorted(
        f for f in os.listdir(image_dir)
        if f.lower().endswith(extensions)
    )
    if not files:
        raise FileNotFoundError(f"No images found in '{image_dir}'")

    print(f"Found {len(files)} image(s): {files}")
    return [prepare_image(os.path.join(image_dir, f)) for f in files]


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    IMAGE_DIR  = "."   # folder containing your sheet music PNGs
    CYCLES     = 20    # full run-throughs before stopping
    PAGE_DELAY = 10    # seconds per page
    TEXT_DELAY = 5     # seconds to show text screens

    # ── Init display ─────────────────────────────────────────────────────────
    epd = epd10in2g.EPD()
    epd.init()
    print("Display initialized.")

    # ── Determine fastest available display method ────────────────────────────
    if hasattr(epd, "display_fast"):
        display_fn = epd.display_fast
        print("Using display_fast()")
    elif hasattr(epd, "displayPartial"):
        display_fn = epd.displayPartial
        print("Using displayPartial()")
    elif hasattr(epd, "display_Partial"):
        display_fn = epd.display_Partial
        print("Using display_Partial()")
    else:
        display_fn = epd.display
        print("Falling back to display()")

    # ── Pre-buffer everything before the loop ────────────────────────────────
    print("Pre-buffering images...")
    images      = load_images(IMAGE_DIR)
    page_buffers = [epd.getbuffer(img) for img in images]

    # Text screens — edit these to match your piece
    title_buffer = epd.getbuffer(make_text_screen([
        "Pepper Note",
        "Proof of Concept",
        "Confidential"
    ], font_size=56))

    end_buffer = epd.getbuffer(make_text_screen(
        "End of Excerpt", font_size=48
    ))

    print(f"Buffered {len(page_buffers)} page(s) + 2 text screen(s). Starting loop.")

    # ── Main loop ─────────────────────────────────────────────────────────────
    count = 0
    try:
        while count < CYCLES:
            print(f"\n── Cycle {count + 1}/{CYCLES} ──")

            # Show title screen at the start of each cycle
            print("Displaying title screen...")
            display_fn(title_buffer)
            time.sleep(TEXT_DELAY)

            # Display each sheet music page
            for i, buf in enumerate(page_buffers):
                print(f"Page {i + 1}/{len(page_buffers)}")
                display_fn(buf)
                time.sleep(PAGE_DELAY)

            # Show end screen at the close of each cycle
            print("Displaying end screen...")
            display_fn(end_buffer)
            time.sleep(TEXT_DELAY)

            count += 1

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    finally:
        print("Clearing display and sleeping...")
        epd.Clear()
        epd.sleep()
        print("Done.")


if __name__ == "__main__":
    main()