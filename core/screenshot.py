import os
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


def start_long_screenshot(root):
    root.withdraw()
    threading.Thread(target=select_area_for_long_screenshot, args=(root,)).start()


def select_area_for_long_screenshot(root):
    global long_screenshot_coords
    import ctypes

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
        root.after(0, lambda: show_long_screenshot_window(root))

    canvas.bind("<ButtonPress-1>", on_click)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    screen.mainloop()


def show_long_screenshot_window(root):
    overlay = show_overlay_box(long_screenshot_coords, root)

    def capture_current_view():
        # Get updated geometry of the overlay
        geo = overlay.geometry()  # Format: "widthxheight+x+y"
        size_part, pos_part = geo.split("+", 1)
        width, height = map(int, size_part.split("x"))
        x, y = map(int, pos_part.split("+"))

        overlay.withdraw()  # Hide before screenshot
        time.sleep(0.2)

        screenshot = pyautogui.screenshot()
        cropped = screenshot.crop((x, y, x + width, y + height))
        long_screenshot_images.append(
            cv2.cvtColor(np.array(cropped), cv2.COLOR_RGB2BGR)
        )

        overlay.deiconify()  # Show again
        status_label.config(text=f"✅ Captured {len(long_screenshot_images)} parts")

    def finish_and_save():
        overlay.destroy()  # close the overlay window
        stop_auto_scroll_capture()
        if not long_screenshot_images:
            messagebox.showwarning("Empty", "No captures taken.")
            return

        # 1. Find max width
        max_width = max(img.shape[1] for img in long_screenshot_images)

        # 2. Pad images to match max width
        padded_images = []
        for img in long_screenshot_images:
            height, width, channels = img.shape
            if width < max_width:
                # Pad on the right
                pad_width = max_width - width
                padded = cv2.copyMakeBorder(
                    img,
                    top=0,
                    bottom=0,
                    left=0,
                    right=pad_width,
                    borderType=cv2.BORDER_CONSTANT,
                    value=(0, 0, 0),  # Black padding, change to (255,255,255) for white
                )
                padded_images.append(padded)
            else:
                padded_images.append(img)

        # 3. Stack and save
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
        overlay.withdraw()  # Hide overlay for clean screenshots
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
