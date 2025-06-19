import threading
import time
from tkinter import filedialog, messagebox

import cv2
import numpy as np
import pyautogui
from PIL import Image, ImageChops, ImageStat

is_auto_capture_active = True


def start_auto_scroll_screenshot(root, coords, storage_list):
    global is_auto_capture_active
    is_auto_capture_active = True
    threading.Thread(
        target=_manual_scroll_capture_loop, args=(root, coords, storage_list)
    ).start()


def stop_auto_scroll_capture():
    global is_auto_capture_active
    is_auto_capture_active = False


def _manual_scroll_capture_loop(root, coords, storage_list):
    global is_auto_capture_active
    x1, y1, x2, y2 = coords

    prev_img = None
    scroll_threshold = 30  # Minimum Y-difference in pixels

    while is_auto_capture_active:
        screenshot = pyautogui.screenshot()
        cropped = screenshot.crop((x1, y1, x2, y2))
        current_np = np.array(cropped)
        print(cropped)
        if prev_img is None:
            prev_img = current_np
            storage_list.append(cv2.cvtColor(current_np, cv2.COLOR_RGB2BGR))
        else:
            # Compare a small vertical slice
            diff = cv2.absdiff(prev_img, current_np)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_RGB2GRAY)
            non_zero_count = np.count_nonzero(gray_diff)

            if non_zero_count > 10000:  # Tune this threshold for sensitivity
                storage_list.append(cv2.cvtColor(current_np, cv2.COLOR_RGB2BGR))
                prev_img = current_np

        time.sleep(0.5)

    # Done capturing
    root.after(0, lambda: messagebox.showinfo("Done", "Auto scroll capture finished."))
