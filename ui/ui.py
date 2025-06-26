import tkinter as tk
from tkinter import ttk

from core.preview_canvas import ImagePreviewCanvas
from core.screenshot_manager import ScreenshotManager


def start_ui():
    root = tk.Tk()
    root.title("Custom Screenshot Stitcher")
    root.configure(bg="#1e1e1e")
    root.geometry("1000x700")

    # 🧱 Main horizontal frame (split left & right)
    main_frame = tk.Frame(root, bg="#1e1e1e")
    main_frame.pack(fill="both", expand=True)

    # 🔹 Left side (buttons + big preview)
    left_frame = tk.Frame(main_frame, bg="#1e1e1e")
    left_frame.pack(side="left", fill="both", expand=True)

    # 🎛️ Top button bar
    button_frame = tk.Frame(left_frame, bg="#1e1e1e")
    button_frame.pack(pady=10)

    preview_canvas = ImagePreviewCanvas(left_frame)

    # ✅ Get the canvas widget and pack it into the UI
    canvas_widget = preview_canvas.get_widget()
    canvas_widget.pack(pady=10, padx=10, fill="both", expand=True)

    # 🔸 Right side - thumbnail panel
    right_frame = tk.Frame(main_frame, bg="#1e1e1e", width=200)
    right_frame.pack(side="right", fill="y")

    tk.Label(right_frame, text="Captured Parts", bg="#1e1e1e", fg="#ffffff").pack(
        pady=5
    )

    # 🖱️ Scrollable thumbnail list
    canvas = tk.Canvas(right_frame, bg="#1e1e1e", highlightthickness=0)
    scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
    thumbnail_frame = tk.Frame(canvas, bg="#1e1e1e")

    thumbnail_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=thumbnail_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="y", expand=True)
    scrollbar.pack(side="right", fill="y")

    # ✅ Initialize Screenshot Manager (after all widgets are created)
    manager = ScreenshotManager(root, preview_canvas, thumbnail_frame)

    # 🔘 Button: Start Long Screenshot (calls class method)
    tk.Button(
        button_frame,
        text="Start Long Screenshot",
        command=manager.start,
        bg="#2c2c2c",
        fg="#e0e0e0",
        activebackground="#444444",
        activeforeground="#e0e0e0",
        relief=tk.FLAT,
    ).pack(side=tk.LEFT)

    tk.Button(
        button_frame,
        text="🖼️ Export Canvas",
        command=lambda: preview_canvas.export_canvas_as_image(),
        bg="#2c2c2c",
        fg="#e0e0e0",
        activebackground="#444444",
        activeforeground="#e0e0e0",
        relief=tk.FLAT,
    ).pack(side=tk.LEFT)

    root.mainloop()
