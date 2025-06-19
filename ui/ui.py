import tkinter as tk

from core.screenshot import start_long_screenshot


def start_ui():
    root = tk.Tk()
    root.title("Custom Screenshot Stitcher")
    root.configure(bg="#1e1e1e")
    root.geometry("640x900")

    frame = tk.Frame(root, bg="#1e1e1e")
    frame.pack(pady=10)

    tk.Button(
        frame,
        text="Start Long Screenshot",
        command=lambda: start_long_screenshot(root),
        bg="#2c2c2c",
        fg="#e0e0e0",
        activebackground="#444444",
        activeforeground="#e0e0e0",
        relief=tk.FLAT,
    ).pack(side=tk.LEFT)

    preview_label = tk.Label(
        root,
        text="Preview will appear here",
        bg="#2b2b2b",
        fg="#e0e0e0",
        width=80,
        height=40,
    )
    preview_label.pack(pady=10, padx=10, fill="both", expand=True)

    root.mainloop()
