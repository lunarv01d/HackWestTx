from tkinter import *
import os


window_width = 200
window_height = 200



root = Tk()
img = PhotoImage(file="window/assets/Pot.png")
root.title("Taskagochi")
root.geometry(f"{window_width}x{window_height}+0-0")
image_label = Label(root, image=img)
image_label.pack()
root.overrideredirect(1)



root.mainloop()
