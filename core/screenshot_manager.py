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


class ScreenshotManager:
    def __init__(self, root, preview_canvas, thumbnail_container):
        self.root = root
        self.preview_canvas = preview_canvas
        self.thumbnail_container = thumbnail_container

        self.coords = None
        self.images = []
        self.thumbnail_refs = []

    def start(self):
        self.root.withdraw()
        threading.Thread(target=self._select_area).start()

    def _select_area(self):
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
            canvas_x = screen.winfo_rootx()
            canvas_y = screen.winfo_rooty()
            x1, y1 = start_x + canvas_x, start_y + canvas_y  # type: ignore
            x2, y2 = event.x + canvas_x, event.y + canvas_y
            self.coords = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            screen.withdraw()
            screen.update_idletasks()
            time.sleep(0.2)
            screen.destroy()
            self.root.after(0, self._show_capture_ui)

        canvas.bind("<ButtonPress-1>", on_click)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)

        screen.mainloop()

    def _show_capture_ui(self):
        overlay = show_overlay_box(self.coords, self.root)

        def capture():
            geo = overlay.geometry()
            size_part, pos_part = geo.split("+", 1)
            width, height = map(int, size_part.split("x"))
            x, y = map(int, pos_part.split("+"))

            overlay.withdraw()
            time.sleep(0.2)

            screenshot = pyautogui.screenshot()
            cropped = screenshot.crop((x, y, x + width, y + height))
            img_np = cv2.cvtColor(np.array(cropped), cv2.COLOR_RGB2BGR)
            self.images.append(img_np)

            overlay.deiconify()
            status_label.config(text=f"✅ Captured {len(self.images)} parts")

            thumb = cropped.copy()
            thumb.thumbnail((240, 180))
            thumb_tk = ImageTk.PhotoImage(thumb)
            self.thumbnail_refs.append(thumb_tk)

            thumb_label = tk.Label(
                self.thumbnail_container, image=thumb_tk, bg="#333333", cursor="hand2"
            )
            thumb_label.pack(pady=4, padx=4)

            def on_click_thumb(image=cropped):
                preview = image.copy()
                preview.thumbnail((600, 400))
                self.preview_canvas.add_image(preview)  # Pass the PIL Image directly

            thumb_label.bind("<Button-1>", lambda e: on_click_thumb())

        def finish():
            overlay.destroy()
            stop_auto_scroll_capture()
            if not self.images:
                messagebox.showwarning("Empty", "No captures taken.")
                return

            max_width = max(img.shape[1] for img in self.images)
            padded = [
                (
                    cv2.copyMakeBorder(
                        img,
                        0,
                        0,
                        0,
                        max_width - img.shape[1],
                        cv2.BORDER_CONSTANT,
                        value=(0, 0, 0),
                    )
                    if img.shape[1] < max_width
                    else img
                )
                for img in self.images
            ]

            final = np.vstack(padded)
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png", filetypes=[("PNG Image", "*.png")]
            )
            if save_path:
                cv2.imwrite(save_path, final)
                messagebox.showinfo("Saved", f"Long screenshot saved:\n{save_path}")

            window.destroy()
            self.images.clear()
            self.root.deiconify()

        def undo():
            if self.images:
                self.images.pop()
                status_label.config(
                    text=f"⏪ Undid last capture. {len(self.images)} left."
                )
            else:
                messagebox.showinfo("Nothing to undo", "No captured images to undo.")

        def auto_scroll():
            overlay.withdraw()
            start_auto_scroll_screenshot(self.root, self.coords, self.images)

        def on_close():
            stop_auto_scroll_capture()
            overlay.destroy()
            window.destroy()
            self.root.deiconify()

        window = tk.Toplevel(self.root)
        window.title("Long Screenshot Capture")
        window.geometry("300x180")
        window.resizable(False, False)
        window.protocol("WM_DELETE_WINDOW", on_close)

        tk.Label(window, text="Scroll and press capture repeatedly").pack(pady=10)
        tk.Button(window, text="📸 Capture Current View", command=capture).pack(pady=5)
        tk.Button(window, text="⚙️ Start Auto Scroll", command=auto_scroll).pack(pady=5)
        tk.Button(window, text="✅ Finish & Save", command=finish).pack(pady=5)
        tk.Button(window, text="⏪ Undo Last", command=undo).pack(pady=5)

        global status_label
        status_label = tk.Label(window, text="No captures yet.")
        status_label.pack(pady=5)
