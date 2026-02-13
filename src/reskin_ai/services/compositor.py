from __future__ import annotations

import io


def render_tattoo_overlay_preview(
    *,
    base_image_bytes: bytes,
    scar_mask_bytes: bytes,
    tattoo_image_bytes: bytes,
    max_edge: int = 1024,
) -> bytes:
    # Pillow is optional for local dev (Windows Python 3.14 may not have wheels yet).
    # In production Docker we install the `render` extra.
    from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps  # type: ignore

    def fit_within(size: tuple[int, int], edge: int) -> tuple[int, int]:
        w, h = size
        if w <= 0 or h <= 0:
            return (edge, edge)
        scale = min(edge / w, edge / h, 1.0)
        return (max(1, int(round(w * scale))), max(1, int(round(h * scale))))

    def estimate_white_background_alpha(img_rgba: Image.Image) -> Image.Image:
        w, h = img_rgba.size
        if w < 8 or h < 8:
            return img_rgba
        corners = [
            img_rgba.getpixel((2, 2)),
            img_rgba.getpixel((w - 3, 2)),
            img_rgba.getpixel((2, h - 3)),
            img_rgba.getpixel((w - 3, h - 3)),
        ]
        corner_luma = sum(int(0.2126 * r + 0.7152 * g + 0.0722 * b) for r, g, b, _a in corners) / 4.0
        if corner_luma < 235:
            return img_rgba

        lum = ImageOps.grayscale(img_rgba)
        alpha = ImageOps.invert(lum).point(lambda p: 0 if p < 20 else min(255, int(p * 1.4)))
        rgb = img_rgba.convert("RGB")
        out = Image.merge("RGBA", (*rgb.split(), alpha))
        return out

    def crop_to_visible(img_rgba: Image.Image) -> Image.Image:
        alpha = img_rgba.getchannel("A")
        bbox = alpha.getbbox()
        if bbox is None:
            return img_rgba
        x0, y0, x1, y1 = bbox
        # Avoid overly tight crops that can clip strokes
        pad = max(2, int(round(max(x1 - x0, y1 - y0) * 0.03)))
        x0 = max(0, x0 - pad)
        y0 = max(0, y0 - pad)
        x1 = min(img_rgba.size[0], x1 + pad)
        y1 = min(img_rgba.size[1], y1 + pad)
        return img_rgba.crop((x0, y0, x1, y1))

    def extract_ink_mask(img_rgba: Image.Image) -> Image.Image:
        """
        Convert a generated "design image" into a clean ink mask.
        Goal: avoid mosaic-like background noise by keeping only dark strokes.
        """
        # Start from luminance so color backgrounds do not leak into alpha.
        lum = ImageOps.grayscale(img_rgba)
        lum = ImageOps.autocontrast(lum)

        # Turn "dark pixels" into "ink" (higher = more ink).
        ink = ImageOps.invert(lum)

        # Suppress speckle noise and keep strokes.
        ink = ink.filter(ImageFilter.MedianFilter(size=3))
        ink = ImageEnhance.Contrast(ink).enhance(1.65)

        # Hard-threshold low ink levels to avoid "smudged" look on skin.
        ink = ink.point(lambda p: 0 if p < 36 else min(255, int((p - 28) * 1.35)))

        # Slight blur makes edges feel more natural when blended.
        ink = ink.filter(ImageFilter.GaussianBlur(radius=0.7))
        return ink

    base = Image.open(io.BytesIO(base_image_bytes)).convert("RGBA")
    target_size = fit_within(base.size, edge=max_edge)
    if target_size != base.size:
        base = base.resize(target_size, resample=Image.Resampling.LANCZOS)

    mask = Image.open(io.BytesIO(scar_mask_bytes)).convert("L")
    if mask.size != base.size:
        mask = mask.resize(base.size, resample=Image.Resampling.NEAREST)
    mask = mask.point(lambda p: 255 if p > 16 else 0)
    soft_mask = mask.filter(ImageFilter.GaussianBlur(radius=6))

    bbox = mask.getbbox()
    if bbox is None:
        out = io.BytesIO()
        base.save(out, format="PNG", optimize=True)
        return out.getvalue()

    x0, y0, x1, y1 = bbox
    bw = max(1, x1 - x0)
    bh = max(1, y1 - y0)
    pad = int(round(max(bw, bh) * 0.12))
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(base.size[0], x1 + pad)
    y1 = min(base.size[1], y1 + pad)
    bw = max(1, x1 - x0)
    bh = max(1, y1 - y0)

    tattoo = Image.open(io.BytesIO(tattoo_image_bytes)).convert("RGBA")
    tattoo = estimate_white_background_alpha(tattoo)
    tattoo = crop_to_visible(tattoo)

    # Convert arbitrary provider output into a clean "ink-only" layer.
    ink_alpha = extract_ink_mask(tattoo)

    tw, th = tattoo.size
    scale = min(bw / tw, bh / th, 1.0)
    new_size = (max(1, int(round(tw * scale))), max(1, int(round(th * scale))))
    if new_size != tattoo.size:
        tattoo = tattoo.resize(new_size, resample=Image.Resampling.LANCZOS)
        ink_alpha = ink_alpha.resize(new_size, resample=Image.Resampling.LANCZOS)

    overlay_alpha = Image.new("L", base.size, 0)
    px = x0 + (bw - tattoo.size[0]) // 2
    py = y0 + (bh - tattoo.size[1]) // 2
    overlay_alpha.paste(ink_alpha, (px, py))

    # Respect the user's scar mask and keep the preview gentle.
    overlay_alpha = ImageChops.multiply(overlay_alpha, soft_mask)
    overlay_alpha = overlay_alpha.point(lambda p: min(255, int(p * 0.52)))

    # Multiply blend for ink-on-skin feel:
    # - Compute multiply(base, ink_color)
    # - Composite it over base using overlay_alpha as mask
    base_rgb = base.convert("RGB")
    ink_color = Image.new("RGB", base.size, (44, 35, 40))  # warm deep ink
    multiplied = ImageChops.multiply(base_rgb, ink_color)
    composed_rgb = Image.composite(multiplied, base_rgb, overlay_alpha)
    composed = composed_rgb.convert("RGBA")
    out = io.BytesIO()
    composed.save(out, format="PNG", optimize=True)
    return out.getvalue()
