from tkinter import *
import os


window_width = 200
window_height = 200



root = Tk()
img = PhotoImage(file="window/assets/Pot.png")
root.title("Taskagochi")
root.geometry(f"{window_width}x{window_height}+0-0")
root.wm_attributes("-topmost", True)
root.wm_attributes("-alpha", 0.5)
image_label = Label(root, image=img)
image_label.pack()
root.config(bg='')
root.wm_attributes("-transparent", True)


root.mainloop()
