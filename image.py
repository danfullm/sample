from PIL import Image, ImageEnhance, ImageFilter
import time
import os
from waveshare_epd import epd10in2g

# ── Display dimensions ──────────────────────────────────────────────────────
WIDTH, HEIGHT = 960, 640

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

    # Convert to pure 1-bit B&W with dithering disabled (faster, crisper for music)
    img = img.convert("1", dither=Image.Dither.NONE)

    # Driver expects "RGB" mode buffer — convert back
    return img.convert("RGB")


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


def main():
    IMAGE_DIR   = "."   # folder containing your sheet music PNGs
    CYCLES      = 20    # full run-throughs before stopping
    PAGE_DELAY  = 10    # seconds per page

    # ── Init display ────────────────────────────────────────────────────────
    epd = epd10in2g.EPD()
    epd.init()
    print("Display initialized.")

    # ── Pre-process & buffer ALL images before the loop ─────────────────────
    # This is the key optimization: getbuffer() is called once per image,
    # not once per display call.
    print("Pre-buffering images...")
    images  = load_images(IMAGE_DIR)
    buffers = [epd.getbuffer(img) for img in images]
    print(f"Buffered {len(buffers)} page(s). Starting display loop.")

    # ── Determine fastest available display method ───────────────────────────
    # Prefer fast/partial methods if the driver exposes them
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
        print("Falling back to display() — consider a B&W-only driver for faster refresh")

    # ── Main loop ────────────────────────────────────────────────────────────
    count = 0
    try:
        while count < CYCLES:
            for i, buf in enumerate(buffers):
                print(f"Cycle {count + 1}/{CYCLES} — Page {i + 1}/{len(buffers)}")
                display_fn(buf)
                time.sleep(PAGE_DELAY)
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