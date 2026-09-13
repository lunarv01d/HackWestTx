import sys
import subprocess
import importlib.util
import pystray
from PIL import Image

def install_dependencies():
    required_packages = {
        "Pystray": "Pystray",
        "pillow": "pillow",
    }

    missing_packages = []

    for import_name, pip_name in required_packages.items():
        if importlib.util.find_spec(import_name) is None:
            missing_packages.append(pip_name)

    if not missing_packages:
        return

    print("Taskagotchi is missing required components:")

    for package in missing_packages:
        print(f"  - {package}")

    print("\nInstalling required components...")

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "--version"],
            stdout=subprocess.DEVNULL,
        )

    except subprocess.CalledProcessError:
        print("pip was not found. Attempting to install pip...")

        subprocess.check_call(
            [sys.executable, "-m", "ensurepip", "--upgrade"]
        )

    try:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                *missing_packages,
            ]
        )

    except subprocess.CalledProcessError:
        print("\nCould not install Taskagotchi dependencies.")
        print("Check your internet connection and Python permissions.")
        sys.exit(1)

    print("\nDependencies installed successfully!\n")

install_dependencies()

iconImage = Image.open("TrayIcon.png")

def afterClick(icon,query):
    if str(query) == "Ask Gemini":
        return 0
    elif str(query) == "Settings":
        return 0
    elif str(query) == "Quit":
        return 0
icon = pystray.Icon("TG",iconImage,"Taskagotchi", menu=pystray.Menu(pystray.MenuItem("Ask Gemini",afterClick),
pystray.MenuItem("Settings",afterClick),pystray.MenuItem("Quit",afterClick)))

icon.run()