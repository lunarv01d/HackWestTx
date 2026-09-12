from tkinter import *
import sys

window_width = 200
window_height = 200

root = Tk()

root.title("Taskagotchi")
root.geometry(f"{window_width}x{window_height}+0+0")
root.wm_attributes("-topmost", True)
root.overrideredirect(True)

img = PhotoImage(file="window/assets/Pot.png")

if sys.platform == "darwin":
    # macOS
    root.config(bg="systemTransparent")
    root.wm_attributes("-transparent", True)

    image_label = Label(
        root,
        image=img,
        bg="systemTransparent",
        borderwidth=0,
        highlightthickness=0
    )

elif sys.platform == "win32":
    # Windows
    transparent_color = "#ff00ff"

    root.config(bg=transparent_color)
    root.wm_attributes("-transparentcolor", transparent_color)

    image_label = Label(
        root,
        image=img,
        bg=transparent_color,
        borderwidth=0,
        highlightthickness=0
    )

else:
    # Linux fallback
    image_label = Label(
        root,
        image=img,
        borderwidth=0,
        highlightthickness=0
    )

image_label.pack()

root.mainloop()