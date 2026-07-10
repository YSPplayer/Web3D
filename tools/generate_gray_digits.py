#!/usr/bin/env python3
#python .\tools\generate_gray_digits.py D:\YueShaoPu\trainimg2 2000 0.18
import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


WIDTH = 128
HEIGHT = 128
DIGITS_PER_IMAGE = 4


def clamp(value):
    return max(0, min(255, int(value)))


def random_int(rng, min_inclusive, max_inclusive):
    if max_inclusive <= min_inclusive:
        return min_inclusive
    return rng.randint(min_inclusive, max_inclusive)


def random_double(rng, min_inclusive, max_inclusive):
    return min_inclusive + rng.random() * (max_inclusive - min_inclusive)


def load_digit_font(font_size, font_index):
    candidates = [
        "arialbd.ttf",
        "timesbd.ttf",
        "courbd.ttf",
        "DejaVuSans-Bold.ttf",
        "DejaVuSerif-Bold.ttf",
        "DejaVuSansMono-Bold.ttf",
    ]
    ordered = candidates[font_index::3] + candidates[:font_index] + candidates[font_index + 1 :]
    for name in ordered:
        try:
            return ImageFont.truetype(name, font_size)
        except OSError:
            continue
    return ImageFont.load_default()


def fill_background(image, rng):
    pixels = image.load()
    base_gray = random_int(rng, 218, 248)
    for y in range(image.height):
        for x in range(image.width):
            pixels[x, y] = clamp(base_gray + random_int(rng, -6, 6))


def draw_interference_lines(draw, width, height, noise_level, digits_per_image, rng):
    line_count = 1 + digits_per_image + round(noise_level * 10.0)
    for _ in range(line_count):
        gray = random_int(rng, 80, 190)
        stroke_width = max(1, int(round(random_double(rng, 0.6, 1.8))))
        x1 = random_int(rng, -width // 4, width)
        y1 = random_int(rng, 0, height)
        x2 = random_int(rng, 0, width + width // 4)
        y2 = random_int(rng, 0, height)
        draw.line((x1, y1, x2, y2), fill=gray, width=stroke_width)


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1], bbox


def draw_single_digit(image, digit, cell_left, cell_width, height, rng):
    min_side = min(cell_width, height)
    min_font_size = max(10, int(min_side * 0.58))
    max_font_size = max(min_font_size, int(min_side * 0.82))
    font_size = random_int(rng, min_font_size, max_font_size)
    font = load_digit_font(font_size, rng.randrange(3))
    text = str(digit)

    scratch = Image.new("L", image.size, 0)
    scratch_draw = ImageDraw.Draw(scratch)
    text_width, text_height, bbox = text_size(scratch_draw, text, font)

    center_x = cell_left + cell_width / 2.0
    center_y = height / 2.0
    x = center_x - text_width / 2.0 + random_double(rng, -cell_width * 0.08, cell_width * 0.08)
    y = (height + text_height) / 2.0 + random_double(rng, -height * 0.08, height * 0.08)
    digit_gray = random_int(rng, 8, 70)

    scratch_draw.text((x - bbox[0], y - bbox[1]), text, font=font, fill=255)

    angle = random_double(rng, -16.0, 16.0)
    scale_x = random_double(rng, 0.88, 1.12)
    scale_y = random_double(rng, 0.88, 1.12)
    transformed = transform_about_center(scratch, center_x, center_y, angle, scale_x, scale_y)

    image_pixels = image.load()
    mask_pixels = transformed.load()
    for py in range(image.height):
        for px in range(image.width):
            alpha = mask_pixels[px, py]
            if alpha:
                current = image_pixels[px, py]
                image_pixels[px, py] = clamp((current * (255 - alpha) + digit_gray * alpha) / 255.0)


def transform_about_center(image, center_x, center_y, angle_degrees, scale_x, scale_y):
    angle = math.radians(angle_degrees)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    a = cos_a * scale_x
    b = -sin_a * scale_y
    d = sin_a * scale_x
    e = cos_a * scale_y

    det = a * e - b * d
    ia = e / det
    ib = -b / det
    id_ = -d / det
    ie = a / det

    c = center_x - a * center_x - b * center_y
    f = center_y - d * center_x - e * center_y
    ic = -(ia * c + ib * f)
    iff = -(id_ * c + ie * f)

    return image.transform(
        image.size,
        Image.AFFINE,
        (ia, ib, ic, id_, ie, iff),
        resample=Image.Resampling.BICUBIC,
        fillcolor=0,
    )


def draw_digits(image, label, rng):
    cell_width = image.width / float(len(label))
    for index, digit in enumerate(label):
        draw_single_digit(image, digit, index * cell_width, cell_width, image.height, rng)


def add_pixel_noise(image, noise_level, rng):
    pixels = image.load()
    changed_pixels = round(image.width * image.height * noise_level * 0.08)
    for _ in range(changed_pixels):
        x = rng.randrange(image.width)
        y = rng.randrange(image.height)
        if rng.choice((True, False)):
            gray = random_int(rng, 0, 70)
        else:
            gray = random_int(rng, 185, 255)
        pixels[x, y] = gray


def maybe_blur(image, rng):
    if rng.random() > 0.35:
        return image
    return image.filter(
        ImageFilter.Kernel(
            (3, 3),
            (
                0.05,
                0.10,
                0.05,
                0.10,
                0.40,
                0.10,
                0.05,
                0.10,
                0.05,
            ),
            scale=1.0,
        )
    )


def create_digit_image(label, noise_level, rng):
    image = Image.new("L", (WIDTH, HEIGHT), 255)
    fill_background(image, rng)
    draw = ImageDraw.Draw(image)
    draw_interference_lines(draw, WIDTH, HEIGHT, noise_level, len(label), rng)
    draw_digits(image, label, rng)
    add_pixel_noise(image, noise_level, rng)
    return maybe_blur(image, rng)


def random_digit_text(rng):
    return "".join(str(rng.randrange(10)) for _ in range(DIGITS_PER_IMAGE))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate 128x128 grayscale 4-digit PNG samples compatible with native Sample::Load."
    )
    parser.add_argument("output_dir", help="Directory where PNG images will be written.")
    parser.add_argument("count", type=int, help="Number of PNG images to generate.")
    parser.add_argument("noise_level", type=float, help="Noise level, same meaning as Java request noiseLevel, 0..1.")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed.")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.count < 1:
        raise ValueError("count must be greater than 0")
    if args.noise_level < 0.0 or args.noise_level > 1.0:
        raise ValueError("noise_level must be between 0 and 1")
    if args.count > 10000:
        raise ValueError("count cannot exceed 10000 when labels are used as unique filenames")

    rng = random.Random(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    used_labels = set()
    for index in range(args.count):
        label = random_digit_text(rng)
        while label in used_labels:
            label = random_digit_text(rng)
        used_labels.add(label)

        image = create_digit_image(label, args.noise_level, rng)
        image.save(output_dir / f"{label}.png")

    print(f"generated={args.count} dir={output_dir} size={WIDTH}x{HEIGHT} noise={args.noise_level}")


if __name__ == "__main__":
    main()
