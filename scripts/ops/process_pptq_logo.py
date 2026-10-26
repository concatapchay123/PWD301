"""Process and generate transparent PPTQ brand assets.

Removes background, removes subtitle 'PEOPLE • PASSION • TEAM • QUALITY',
generates crisp, defringed transparent PNGs, dark/light variants, and favicons.
"""

from pathlib import Path
import numpy as np
from PIL import Image

def process_logo():
    src_path = Path("C:/Users/LENOVO/.gemini/antigravity/brain/3d80f1a4-f9ac-4bd5-9286-2086e55136db/.user_uploaded/media_1792413748465_133d1c04.png")
    if not src_path.is_file():
        raise FileNotFoundError(f"Source image not found: {src_path}")

    img = Image.open(src_path).convert("RGB")
    arr = np.array(img, dtype=np.float32)
    hsv_arr = np.array(img.convert("HSV"), dtype=np.float32)

    s = hsv_arr[:, :, 1]
    v = hsv_arr[:, :, 2]

    # Erase subtitle 'PEOPLE • PASSION • TEAM • QUALITY' in rows >= 335, cols >= 380
    arr[335:, 380:, :3] = [246.0, 252.0, 254.0]
    s[335:, 380:] = 0.0
    v[335:, 380:] = 255.0

    # Calculate smooth alpha based on saturation & darkness
    # Background across image has s <= 12 and v >= 246
    # Logo elements have high saturation (lines, flame) or low brightness (navy text)
    fg_metric = np.maximum(s - 14.0, (244.0 - v) * 1.5)
    alpha = np.clip((fg_metric - 8.0) / (30.0 - 8.0), 0.0, 1.0)

    # De-fringe: unmultiply background color from edge pixels to remove any light halo
    bg_color = np.array([246.0, 252.0, 254.0], dtype=np.float32)
    a_safe = np.maximum(alpha[:, :, None], 1e-3)
    unmixed = np.clip((arr[:, :, :3] - (1.0 - a_safe) * bg_color[None, None, :]) / a_safe, 0.0, 255.0)

    # Reconstruct RGBA
    rgba = np.zeros((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
    rgba[:, :, :3] = unmixed.astype(np.uint8)
    rgba[:, :, 3] = (alpha * 255.0).astype(np.uint8)

    full_im = Image.fromarray(rgba, mode="RGBA")

    # Crop bounding box of non-zero alpha
    rows = np.where(alpha > 0.05)[0]
    cols = np.where(alpha > 0.05)[1]
    pad = 12
    w, h = full_im.size
    crop_rect = (
        max(0, int(cols.min()) - pad),
        max(0, int(rows.min()) - pad),
        min(w, int(cols.max()) + pad),
        min(h, int(rows.max()) + pad),
    )
    logo_full = full_im.crop(crop_rect)

    dest_dir = Path("frontend/assets/img")
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Save standard full logo (Transparent background, dark navy text)
    logo_path = dest_dir / "pptq_logo.png"
    logo_full.save(logo_path, format="PNG", optimize=True)
    print(f"Saved: {logo_path} ({logo_full.size})")

    # 2. Save light theme logo
    logo_light_path = dest_dir / "pptq_logo_light.png"
    logo_full.save(logo_light_path, format="PNG", optimize=True)
    print(f"Saved: {logo_light_path} ({logo_full.size})")

    # 3. Create dark theme variant (crisp bright text for dark backgrounds)
    dark_arr = np.array(logo_full, dtype=np.float32)
    # Text is on the right side (col > 240 in cropped image) with low brightness
    text_mask = (dark_arr[:, :, 3] > 40) & (dark_arr[:, :, 0] < 80) & (dark_arr[:, :, 1] < 80) & (dark_arr[:, :, 2] < 90)
    col_grid = np.arange(dark_arr.shape[1])[None, :]
    text_mask = text_mask & (col_grid > 230)
    
    dark_arr[text_mask, 0] = 248.0
    dark_arr[text_mask, 1] = 250.0
    dark_arr[text_mask, 2] = 252.0

    logo_dark = Image.fromarray(dark_arr.astype(np.uint8), mode="RGBA")
    logo_dark_path = dest_dir / "pptq_logo_dark.png"
    logo_dark.save(logo_dark_path, format="PNG", optimize=True)
    print(f"Saved: {logo_dark_path} ({logo_dark.size})")

    # 4. Extract Shield-only icon (square aspect ratio)
    shield_rows = np.where(alpha[:, :390] > 0.05)[0]
    shield_cols = np.where(alpha[:, :390] > 0.05)[1]
    shield_box = (
        max(0, int(shield_cols.min()) - pad),
        max(0, int(shield_rows.min()) - pad),
        min(w, int(shield_cols.max()) + pad),
        min(h, int(shield_rows.max()) + pad),
    )
    shield_im = full_im.crop(shield_box)
    
    # Make square
    sw, sh = shield_im.size
    max_dim = max(sw, sh) + 12
    square_im = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))
    offset_x = (max_dim - sw) // 2
    offset_y = (max_dim - sh) // 2
    square_im.paste(shield_im, (offset_x, offset_y))

    icon_path = dest_dir / "pptq_icon.png"
    square_im.save(icon_path, format="PNG", optimize=True)
    print(f"Saved: {icon_path} ({square_im.size})")

    # 5. Generate Favicons
    fav_png = dest_dir / "favicon.png"
    square_im.resize((64, 64), Image.Resampling.LANCZOS).save(fav_png, format="PNG", optimize=True)
    print(f"Saved: {fav_png}")

    fav_ico = dest_dir / "favicon.ico"
    square_im.save(fav_ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"Saved: {fav_ico}")

    # Root favicon as well for direct browser requests /favicon.ico
    square_im.save("frontend/favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])

    # 6. Generate PDF watermark (semi-transparent)
    watermark_arr = np.array(logo_full, dtype=np.float32)
    watermark_arr[:, :, 3] = watermark_arr[:, :, 3] * 0.12
    watermark_im = Image.fromarray(watermark_arr.astype(np.uint8), mode="RGBA")
    wm_path = dest_dir / "pptq_logo_watermark.png"
    watermark_im.save(wm_path, format="PNG", optimize=True)
    print(f"Saved: {wm_path}")

if __name__ == "__main__":
    process_logo()
