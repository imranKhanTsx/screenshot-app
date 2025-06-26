import ctypes
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
import numpy as np
import pyautogui
from PIL import Image, ImageTk

from core.overlay import show_overlay_box
from core.screenshot_auto import start_auto_scroll_screenshot, stop_auto_scroll_capture

long_screenshot_coords = None
long_screenshot_images = []
thumbnail_refs = []


def start_long_screenshot(root, big_preview_label, thumbnail_container):
    root.withdraw()
    threading.Thread(
        target=select_area_for_long_screenshot,
        args=(root, big_preview_label, thumbnail_container),
    ).start()


def select_area_for_long_screenshot(root, big_preview_label, thumbnail_container):
    global long_screenshot_coords

    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    screen = tk.Tk()
    screen.attributes("-fullscreen", True)
    screen.attributes("-alpha", 0.3)
    screen.config(bg="black")
    screen.lift()
    screen.attributes("-topmost", True)

    canvas = tk.Canvas(screen, cursor="cross", bg="black")
    canvas.pack(fill=tk.BOTH, expand=True)

    start_x = start_y = None

    def on_click(event):
        nonlocal start_x, start_y
        start_x, start_y = event.x, event.y

    def on_drag(event):
        canvas.delete("rect")
        canvas.create_rectangle(start_x, start_y, event.x, event.y, outline="green", width=2, tag="rect")  # type: ignore

    def on_release(event):
        global long_screenshot_coords
        canvas_x = screen.winfo_rootx()
        canvas_y = screen.winfo_rooty()

        x1, y1 = start_x + canvas_x, start_y + canvas_y  # type: ignore
        x2, y2 = event.x + canvas_x, event.y + canvas_y

        long_screenshot_coords = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

        screen.withdraw()
        screen.update_idletasks()
        time.sleep(0.2)

        screen.destroy()
        root.after(
            0,
            lambda: show_long_screenshot_window(
                root, big_preview_label, thumbnail_container
            ),
        )

    canvas.bind("<ButtonPress-1>", on_click)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    screen.mainloop()


def show_long_screenshot_window(root, big_preview_label, thumbnail_container):
    overlay = show_overlay_box(long_screenshot_coords, root)

    def capture_current_view():
        geo = overlay.geometry()
        size_part, pos_part = geo.split("+", 1)
        width, height = map(int, size_part.split("x"))
        x, y = map(int, pos_part.split("+"))

        overlay.withdraw()
        time.sleep(0.2)

        screenshot = pyautogui.screenshot()
        cropped = screenshot.crop((x, y, x + width, y + height))

        # 1. Convert and store full image (OpenCV format for merging)
        img_np = cv2.cvtColor(np.array(cropped), cv2.COLOR_RGB2BGR)
        long_screenshot_images.append(img_np)

        overlay.deiconify()
        status_label.config(text=f"✅ Captured {len(long_screenshot_images)} parts")

        # 2. Create thumbnail for preview
        thumb = cropped.copy()
        thumb.thumbnail((240, 180))  # Adjust size if needed
        thumb_tk = ImageTk.PhotoImage(thumb)
        thumbnail_refs.append(thumb_tk)  # Prevent garbage collection

        # 3. Create thumbnail label and add click event
        thumb_label = tk.Label(
            thumbnail_container, image=thumb_tk, bg="#333333", cursor="hand2"
        )
        thumb_label.pack(pady=4, padx=4)

        def on_thumbnail_click(image=cropped):
            # Show the selected image in the big preview area
            preview = image.copy()
            preview.thumbnail((600, 400))
            preview_tk = ImageTk.PhotoImage(preview)
            big_preview_label.configure(image=preview_tk, text="")
            big_preview_label.image = preview_tk  # type: ignore # Keep reference

        thumb_label.bind("<Button-1>", lambda e: on_thumbnail_click())

    def finish_and_save():
        overlay.destroy()
        stop_auto_scroll_capture()
        if not long_screenshot_images:
            messagebox.showwarning("Empty", "No captures taken.")
            return

        max_width = max(img.shape[1] for img in long_screenshot_images)

        padded_images = []
        for img in long_screenshot_images:
            height, width, channels = img.shape
            if width < max_width:

                pad_width = max_width - width
                padded = cv2.copyMakeBorder(
                    img,
                    top=0,
                    bottom=0,
                    left=0,
                    right=pad_width,
                    borderType=cv2.BORDER_CONSTANT,
                    value=(0, 0, 0),
                )
                padded_images.append(padded)
            else:
                padded_images.append(img)

        final = np.vstack(padded_images)
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG Image", "*.png")]
        )
        if save_path:
            cv2.imwrite(save_path, final)
            messagebox.showinfo("Saved", f"Long screenshot saved:\n{save_path}")

        window.destroy()
        long_screenshot_images.clear()
        root.deiconify()

    def undo_last_capture():
        if long_screenshot_images:
            long_screenshot_images.pop()
            status_label.config(
                text=f"⏪ Undid last capture. {len(long_screenshot_images)} left."
            )
        else:
            messagebox.showinfo("Nothing to undo", "No captured images to undo.")

    def handle_auto_scroll():
        overlay.withdraw()
        start_auto_scroll_screenshot(
            root, long_screenshot_coords, long_screenshot_images
        )

    def on_close_capture_window():
        stop_auto_scroll_capture()
        overlay.destroy()
        window.destroy()
        root.deiconify()

    window = tk.Toplevel(root)
    window.title("Long Screenshot Capture")
    window.geometry("300x180")
    window.resizable(False, False)
    window.protocol("WM_DELETE_WINDOW", on_close_capture_window)

    tk.Label(window, text="Scroll and press capture repeatedly").pack(pady=10)
    tk.Button(
        window, text="📸 Capture Current View", command=capture_current_view
    ).pack(pady=5)

    tk.Button(window, text="⚙️ Start Auto Scroll", command=handle_auto_scroll).pack(
        pady=5
    )

    tk.Button(window, text="✅ Finish & Save", command=finish_and_save).pack(pady=5)
    tk.Button(window, text="⏪ Undo Last", command=undo_last_capture).pack(pady=5)

    global status_label
    status_label = tk.Label(window, text="No captures yet.")
    status_label.pack(pady=5)
