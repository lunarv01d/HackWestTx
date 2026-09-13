import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging"
SOURCE = ROOT / "trayicon" / "TrayIcon.png"

if not SOURCE.exists():
    raise FileNotFoundError(
        f"Could not find Taskagotchi icon: {SOURCE}"
    )

with Image.open(SOURCE) as source:
    base = source.convert("RGBA")

base = base.resize(
    (1024, 1024),
    Image.Resampling.NEAREST,
)

if sys.platform == "win32":
    output = PACKAGING / "Taskagotchi.ico"

    base.save(
        output,
        format="ICO",
        sizes=[
            (16, 16),
            (24, 24),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        ],
    )

    print(output)

elif sys.platform == "darwin":
    iconset = PACKAGING / "Taskagotchi.iconset"

    if iconset.exists():
        shutil.rmtree(iconset)

    iconset.mkdir(parents=True)

    sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }

    for filename, size in sizes.items():
        image = base.resize(
            (size, size),
            Image.Resampling.NEAREST,
        )

        image.save(
            iconset / filename,
            format="PNG",
        )

    output = PACKAGING / "Taskagotchi.icns"

    subprocess.run(
        [
            "iconutil",
            "-c",
            "icns",
            "-o",
            str(output),
            str(iconset),
        ],
        check=True,
    )

    shutil.rmtree(iconset)

    print(output)

else:
    print(
        "Icon generation is supported on Windows and macOS.",
        file=sys.stderr,
    )
    sys.exit(1)
