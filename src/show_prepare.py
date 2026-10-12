"""See what prepare_image does to one picture, and what its crop throws away.

Problem 2 asks for one of your images next to what prepare_image made of it, and
what the crop cut off. Nothing else in this repository draws that: the sheets
from `clean.py look` show whole pictures, and the web page shows the square the
model sees only after you export a model and open the page in a browser.

    python src/show_prepare.py --image data/clean/amethyst/0007.jpg
    python src/show_prepare.py --scan data/clean          # worst crops first
    python src/show_prepare.py --scan data/clean --sheet  # and draw the worst of them

It takes no arguments of its own beyond these, and nothing else in the
repository works this way: on your own computer run it through uv like every
other command. On an Intel Mac uv cannot install PyTorch at all ("The current
Python platform is not compatible with the lockfile's supported environments"),
so there, and in Colab, run the same commands with `!python` after the cell in
section 3:

    !python src/show_prepare.py --scan data/clean

The first command writes four pictures into long_report/figures/, which is where
long_report.tex looks for them (figures/prepare_original.jpg and
figures/prepare_result.png):

    <stem>_original.jpg        the picture as it was on disk
    <stem>_result.png          the 224 x 224 the model gets, back in colour
    <stem>_cropbox.png         the resized picture with the kept square outlined;
                               everything washed out is thrown away
    <stem>_side_by_side.png    the first two next to each other, for your notes

It also prints the sizes, the rectangle that was kept, how many pixels were cut
off each side and what share of the picture that is. The crop it describes is
measured against prepare_image itself, so the numbers are not a second guess at
the recipe.

`--scan` looks at a whole folder and lists the pictures the crop throws most of
away, which is where to look for the report line "an image where the crop cut
off part of the thing you care about". It deliberately does not try to tell you
whether the stone itself was cut: on this collection every cheap way of guessing
that (how unlike the background the pixels on the crop line are, how busy they
are) put pictures whose stone is safely inside the square above the one picture
that really is cut, so a number would only mislead. Add `--sheet` and it draws
the shortlist as one picture of tiles, each named and measured, which is how the
whole folder gets judged in a minute. Draw any single one with `--image` to see
it at full size.
"""

import argparse
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from torchvision import transforms

from data import CROP, IMAGE_SUFFIXES, MEAN, RESIZE, STD, prepare_image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "long_report" / "figures"
REPORT_WIDTH = 1400    # long side of <stem>_original.jpg, so the report stays small
SHADE = 0.55           # how washed out the thrown-away part looks
TILE = 320             # width of one crop in the contact sheet
COLUMNS = 3            # crops per row in the contact sheet


def font(size):
    for name in ("DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:        # Pillow older than 10.1
        return ImageFont.load_default()


def to_view(x):
    """The prepared array back as a picture. For looking at, not for training."""
    picture = (np.transpose(x, (1, 2, 0)) * np.asarray(STD, dtype=np.float32)
               + np.asarray(MEAN, dtype=np.float32))
    return Image.fromarray(np.clip(picture * 255.0, 0, 255).astype(np.uint8), "RGB")


def resize_and_box(image):
    """Step 2 of the recipe, and the square step 3 keeps out of it.

    The middle is taken after the resize, the way torchvision does it, and the
    rectangle is worked out the way CenterCrop works it out, so it lands on the
    same pixels. check() measures that it does.
    """
    resized = transforms.Resize(RESIZE)(image)
    width, height = resized.size
    left = int(round((width - CROP) / 2))
    top = int(round((height - CROP) / 2))
    return resized, (left, top, left + CROP, top + CROP)


def check(image, resized, box):
    """How far the middle square is from prepare_image's own answer.

    Zero means prepare_image, the crop described here, and torchvision's own
    ImageNet recipe for ResNet18 all agree pixel for pixel.
    """
    from torchvision.models import ResNet18_Weights

    crop = resized.crop(box)
    here = np.asarray(transforms.Compose([transforms.ToTensor(),
                                          transforms.Normalize(MEAN, STD)])(crop),
                      dtype=np.float32)
    prepared = prepare_image(image)
    reference = ResNet18_Weights.IMAGENET1K_V1.transforms()(image).numpy()
    return dict(crop_vs_prepare=float(np.abs(here - prepared).max()),
                prepare_vs_torchvision=float(np.abs(prepared - reference).max()))


def measure(path, compare=True):
    """Everything the report wants to know about one file.

    compare catches the crop up against prepare_image and against torchvision's
    own recipe. It costs two more runs through the picture, which is what the
    report wants for one file and what a scan of a whole folder does not need.
    """
    with Image.open(path) as opened:
        orientation = opened.getexif().get(274, 1)     # 274 is Orientation
        image = opened.convert("RGB")
    resized, box = resize_and_box(image)
    width, height = image.size
    return dict(
        path=Path(path), image=image, resized=resized, box=box,
        orientation=orientation,
        original=(width, height), resized_size=resized.size,
        diffs=check(image, resized, box) if compare else {},
        cut=(box[0], resized.width - box[2], box[1], resized.height - box[3]),
        kept_share=(CROP * CROP) / float(resized.width * resized.height),
        scale_x=width / resized.width, scale_y=height / resized.height,
    )


def cropbox_picture(data):
    """The resized picture: the kept square as it is, the rest washed out."""
    size = data["resized"].size
    sheet = Image.blend(data["resized"], Image.new("RGB", size, "white"), SHADE)
    sheet.paste(data["resized"].crop(data["box"]), (data["box"][0], data["box"][1]))
    draw = ImageDraw.Draw(sheet)
    draw.rectangle((data["box"][0], data["box"][1],
                    data["box"][2] - 1, data["box"][3] - 1),
                   outline=(200, 20, 20), width=3)
    draw.rectangle((0, 0, sheet.width, 24), fill="white")
    draw.text((6, 4), f"{CROP}x{CROP} kept, everything washed out is cut off",
              fill=(0, 0, 0), font=font(16))
    return sheet


def side_by_side_picture(data):
    left = data["image"].copy()
    left.thumbnail((CROP * 4, CROP))
    sheet = Image.new("RGB", (left.width + 12 + data["prepared"].width, CROP), "white")
    sheet.paste(left, (0, 0))
    sheet.paste(data["prepared"], (left.width + 12, 0))
    return sheet


def write_original(data, out, full):
    """The original picture, scaled so the PDF stays small, or copied as it is."""
    if full:
        shutil.copyfile(data["path"], out)
        return
    picture = data["image"].copy()
    picture.thumbnail((REPORT_WIDTH, REPORT_WIDTH))
    picture.save(out, quality=92)


def show(path, out, stem, full):
    data = measure(path)
    data["prepared"] = to_view(prepare_image(data["image"]))
    out.mkdir(parents=True, exist_ok=True)
    write_original(data, out / f"{stem}_original.jpg", full)
    data["prepared"].save(out / f"{stem}_result.png")
    cropbox_picture(data).save(out / f"{stem}_cropbox.png")
    side_by_side_picture(data).save(out / f"{stem}_side_by_side.png")

    left, right, top, bottom = data["cut"]
    across, down = data["resized_size"]
    print(f"\n{data['path']}")
    print(f"  on disk           {data['original'][0]} x {data['original'][1]}")
    print(f"  after Resize(256) {across} x {down}")
    print(f"  square kept       x {data['box'][0]}..{data['box'][2]}, "
          f"y {data['box'][1]}..{data['box'][3]}   ({CROP} x {CROP})")
    print(f"  cut off           {left} left, {right} right, {top} top, {bottom} bottom"
          f"   (in the {across} x {down} picture)")
    print(f"                    {left * data['scale_x']:.0f} left, "
          f"{right * data['scale_x']:.0f} right, {top * data['scale_y']:.0f} top, "
          f"{bottom * data['scale_y']:.0f} bottom"
          f"   (in the {data['original'][0]} x {data['original'][1]} photo)")
    print(f"  kept              {data['kept_share']:.1%} of the area; "
          f"{(left + right) / across:.1%} of the width and "
          f"{(top + bottom) / down:.1%} of the height thrown away")
    print(f"  check             this crop vs prepare_image        "
          f"{data['diffs']['crop_vs_prepare']:.1e}")
    print(f"                    prepare_image vs torchvision       "
          f"{data['diffs']['prepare_vs_torchvision']:.1e}")
    if data["orientation"] != 1:
        print(f"  WARNING           EXIF orientation is {data['orientation']}: the camera "
              "stored the picture\n"
              "                    turned. Image.open does not turn it back, so this "
              "crop is\n"
              "                    the middle of the turned picture.")
    print(f"  wrote             {out}/{stem}_original.jpg, {stem}_result.png, "
          f"{stem}_cropbox.png,\n                    {stem}_side_by_side.png")


def scan(folder, rows):
    paths = sorted(p for p in Path(folder).rglob("*")
                   if p.suffix.lower() in IMAGE_SUFFIXES)
    if not paths:
        raise SystemExit(f"{folder} has no images")
    print(f"{len(paths)} images under {folder}. The crop throws most away from "
          "these,\nso they are where to look for one that cut the stone. The "
          "numbers are the\ncrop's own geometry; whether it cut the stone, the "
          "drawing says, so draw the\nshortlist with --sheet:\n")
    print(f"  {'area kept':>9}  {'on disk':>13}  {'after resize':>13}  "
          "orientation  file")
    measured = []
    for path in paths:
        try:
            measured.append(measure(path, compare=False))   # no equality check for a scan
        except Exception as error:               # a file that is not an image
            print(f"  cannot read {path}: {error}")
    for data in sorted(measured, key=lambda d: d["kept_share"])[:rows]:
        print(f"  {data['kept_share']:>8.1%}  "
              f"{data['original'][0]:>5} x {data['original'][1]:<7}"
              f"{data['resized_size'][0]:>5} x {data['resized_size'][1]:<7}"
              f"{data['orientation']:>11}  {data['path']}")
    turned = [d for d in measured if d["orientation"] != 1]
    print(f"\n{len(turned)} of {len(measured)} carry an EXIF orientation other than 1 "
          "(a phone photo\nstored sideways). prepare_image does not turn those back, so "
          "the model sees them turned:")
    for data in turned[:rows]:
        print(f"  orientation {data['orientation']}  {data['path']}")
    return measured


def sheet_tile(data):
    """One candidate as a small picture: the kept square, the rest washed out."""
    size = data["resized"].size
    tile = Image.blend(data["resized"], Image.new("RGB", size, "white"), SHADE)
    tile.paste(data["resized"].crop(data["box"]), data["box"][:2])
    ImageDraw.Draw(tile).rectangle((data["box"][0], data["box"][1],
                                    data["box"][2] - 1, data["box"][3] - 1),
                                   outline=(200, 20, 20), width=2)
    tile.thumbnail((TILE, TILE * 2))
    return tile


def sheet(measured, out, stem, rows):
    """The worst crops as one picture, so a whole folder can be judged at a glance.

    Fifteen of these take a minute to look at; every picture in data/clean one at
    a time does not. Each tile names its file, how much of the picture the crop
    keeps and what it throws away from each side. The drawings are the evidence;
    the scan's ranking only decides which ones get drawn.
    """
    picks = sorted(measured, key=lambda d: d["kept_share"])[:rows]
    tiles = [(f"{d['path'].parent.name}/{d['path'].stem}", d, sheet_tile(d))
             for d in picks]
    down = max(tile.height for _, _, tile in tiles) + 36
    across = (len(tiles) + COLUMNS - 1) // COLUMNS
    board = Image.new("RGB", (COLUMNS * (TILE + 8) + 8, across * down + 8), "white")
    draw = ImageDraw.Draw(board)
    for index, (name, data, tile) in enumerate(tiles):
        left, right, top, bottom = data["cut"]
        x = 8 + (index % COLUMNS) * (TILE + 8)
        y = 8 + (index // COLUMNS) * down
        board.paste(tile, (x, y + 34))
        draw.text((x, y), name[:46], fill=(0, 0, 0), font=font(13))
        draw.text((x, y + 17), f"keeps {data['kept_share']:.0%}; throws away "
                               f"{left} {right} {top} {bottom}",
                  fill=(160, 20, 20), font=font(13))
    board.save(out / f"{stem}_sheet.png")
    return board.size


def main():
    parser = argparse.ArgumentParser(
        description="Draw what prepare_image keeps and what it throws away.")
    parser.add_argument("--image",
                        help="one picture to draw, e.g. data/clean/amethyst/0007.jpg")
    parser.add_argument("--scan",
                        help="a folder: list the pictures the crop throws most of away")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="where the pictures go")
    parser.add_argument("--stem", default="prepare", help="start of the file names it writes")
    parser.add_argument("--rows", type=int, default=15, help="how many lines --scan prints")
    parser.add_argument("--sheet", action="store_true",
                        help="with --scan, also draw the worst crops as one picture")
    parser.add_argument("--full", action="store_true",
                        help="write the original as it is, not scaled down for the report")
    args = parser.parse_args()
    if not args.image and not args.scan:
        parser.error("give --image, or --scan, or both")
    if args.image:
        if not Path(args.image).is_file():
            raise SystemExit(f"no such file: {args.image}")
        show(Path(args.image), Path(args.out), args.stem, args.full)
    if args.scan:
        measured = scan(args.scan, args.rows)
        if args.sheet and measured:
            out = Path(args.out)
            out.mkdir(parents=True, exist_ok=True)
            size = sheet(measured, out, args.stem, args.rows)
            print(f"\nwrote {out}/{args.stem}_sheet.png ({size[0]} x {size[1]}): the "
                  f"{min(args.rows, len(measured))} worst crops, drawn")


if __name__ == "__main__":
    main()