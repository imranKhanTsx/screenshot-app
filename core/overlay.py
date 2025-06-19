import tkinter as tk


def show_overlay_box(coords, root):
    x1, y1, x2, y2 = coords

    overlay = tk.Toplevel(root)
    overlay.attributes("-topmost", True)
    overlay.overrideredirect(True)
    overlay.geometry(f"{x2 - x1}x{y2 - y1}+{x1}+{y1}")
    overlay.configure(bg="green")
    overlay.attributes("-alpha", 0.3)

    handle_size = 15
    handle = tk.Frame(
        overlay,
        width=handle_size,
        height=handle_size,
        bg="darkgreen",
        cursor="bottom_right_corner",
    )
    handle.place(relx=1.0, rely=1.0, x=-handle_size, y=-handle_size, anchor="se")

    # --- Resize logic ---
    def start_resize(event):
        overlay._start_x = event.x  # type: ignore
        overlay._start_y = event.y  # type: ignore
        overlay._start_width = overlay.winfo_width()  # type: ignore
        overlay._start_height = overlay.winfo_height()  # type: ignore

    def do_resize(event):
        dx = event.x - overlay._start_x  # type: ignore
        dy = event.y - overlay._start_y  # type: ignore
        new_width = max(100, overlay._start_width + dx)  # type: ignore
        new_height = max(100, overlay._start_height + dy)  # type: ignore
        overlay.geometry(
            f"{new_width}x{new_height}+{overlay.winfo_x()}+{overlay.winfo_y()}"
        )
        handle.place(relx=1.0, rely=1.0, x=-handle_size, y=-handle_size, anchor="se")

    handle.bind("<Button-1>", start_resize)
    handle.bind("<B1-Motion>", do_resize)

    # --- Drag logic ---
    def start_drag(event):
        # Ignore drag if clicked on the resize handle
        widget = event.widget
        if (
            widget == handle
            or widget.winfo_containing(event.x_root, event.y_root) == handle
        ):
            overlay._dragging = False  # type: ignore
            return
        overlay._dragging = True  # type: ignore
        overlay._drag_offset_x = event.x  # type: ignore
        overlay._drag_offset_y = event.y  # type: ignore

    def do_drag(event):
        if getattr(overlay, "_dragging", False):
            dx = event.x_root - overlay._drag_offset_x  # type: ignore
            dy = event.y_root - overlay._drag_offset_y  # type: ignore
            overlay.geometry(f"+{dx}+{dy}")

    def stop_drag(event):
        overlay._dragging = False  # type: ignore

    overlay.bind("<Button-1>", start_drag)
    overlay.bind("<B1-Motion>", do_drag)
    overlay.bind("<ButtonRelease-1>", stop_drag)

    return overlay
