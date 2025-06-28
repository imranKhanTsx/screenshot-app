import tkinter as tk


class OverlayBox:
    def __init__(self, coords, root):
        self.root = root
        self.x1, self.y1, self.x2, self.y2 = coords

        self.overlay = tk.Toplevel(root)
        self.overlay.attributes("-topmost", True)
        self.overlay.overrideredirect(True)
        self.overlay.geometry(
            f"{self.x2 - self.x1}x{self.y2 - self.y1}+{self.x1}+{self.y1}"
        )
        self.overlay.configure(bg="green")
        self.overlay.attributes("-alpha", 0.3)

        self._dragging = False
        self._init_resize_handle()
        self._bind_drag()

    def _init_resize_handle(self):
        handle_size = 15
        self.handle = tk.Frame(
            self.overlay,
            width=handle_size,
            height=handle_size,
            bg="darkgreen",
            cursor="bottom_right_corner",
        )
        self.handle.place(
            relx=1.0, rely=1.0, x=-handle_size, y=-handle_size, anchor="se"
        )
        self.handle.bind("<Button-1>", self._start_resize)
        self.handle.bind("<B1-Motion>", self._do_resize)

    def _start_resize(self, event):
        self._start_x = event.x
        self._start_y = event.y
        self._start_width = self.overlay.winfo_width()
        self._start_height = self.overlay.winfo_height()

    def _do_resize(self, event):
        dx = event.x - self._start_x
        dy = event.y - self._start_y
        new_width = max(100, self._start_width + dx)
        new_height = max(100, self._start_height + dy)
        self.overlay.geometry(
            f"{new_width}x{new_height}+{self.overlay.winfo_x()}+{self.overlay.winfo_y()}"
        )
        self.handle.place(relx=1.0, rely=1.0, x=-15, y=-15, anchor="se")

    def _bind_drag(self):
        self.overlay.bind("<Button-1>", self._start_drag)
        self.overlay.bind("<B1-Motion>", self._do_drag)
        self.overlay.bind("<ButtonRelease-1>", self._stop_drag)

    def _start_drag(self, event):
        if (
            event.widget == self.handle
            or event.widget.winfo_containing(event.x_root, event.y_root) == self.handle
        ):
            self._dragging = False
            return
        self._dragging = True
        self._drag_offset_x = event.x
        self._drag_offset_y = event.y

    def _do_drag(self, event):
        if self._dragging:
            dx = event.x_root - self._drag_offset_x
            dy = event.y_root - self._drag_offset_y
            self.overlay.geometry(f"+{dx}+{dy}")

    def _stop_drag(self, event):
        self._dragging = False

    def bring_to_front(self):
        self.overlay.lift()
        self.overlay.attributes("-topmost", True)
        self.overlay.after(100, lambda: self.overlay.attributes("-topmost", False))

    def focus_overlay(self):
        self.overlay.lift()
        self.overlay.focus_force()

    def withdraw(self):
        self.overlay.withdraw()

    def deiconify(self):
        self.overlay.deiconify()

    def destroy(self):
        self.overlay.destroy()

    def geometry(self):
        return self.overlay.geometry()

    def get_widget(self):
        return self.overlay
