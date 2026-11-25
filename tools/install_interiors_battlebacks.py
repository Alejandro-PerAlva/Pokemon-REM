"""Install 6 uploaded interior battlebacks (512x384): IndoorA, IndoorB, Lab, MorfeoBase, Mansion, Temple."""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BB_DIR = ROOT / "Graphics" / "Battlebacks"
UP_DIR = Path(r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded")

INTERIORS = [
    ("IndoorA", UP_DIR / "media_1795619249801_cf9bf2df.png"),
    ("IndoorB", UP_DIR / "media_1795619249799_7ff679dd.png"),
    ("Lab", UP_DIR / "media_1795619249799_19cc71fb.png"),
    ("Mansion", UP_DIR / "media_1795619365585_2484af85.png"),
    ("Temple", UP_DIR / "media_1795619400128_a445239b.png"),
]


def main():
    sheet = Image.new("RGBA", (1560, 840), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)

    for idx, (name, src_path) in enumerate(INTERIORS):
        bg = Image.open(src_path).convert("RGBA")
        bg.save(BB_DIR / f"battlebg{name}.png")

        col = idx % 3
        row = idx // 3
        x0 = 10 + col * 518
        y0 = 26 + row * 416
        draw.text((x0 + 4, y0 - 20), f"{name} (512x384)", fill=(237, 189, 98, 255))
        comp = bg.copy()
        for dx in range(0, 512, 8):
            ImageDraw.Draw(comp).line([(dx, 304), (dx + 4, 304)], fill=(255, 255, 255, 110))
        sheet.alpha_composite(comp, (x0, y0))

    sheet.save(ROOT / "previews" / "interiors_review.png")
    print("Installed 6 interior backgrounds cleanly.")


if __name__ == "__main__":
    main()
