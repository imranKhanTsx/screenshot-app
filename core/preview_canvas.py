import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk


class ImagePreviewCanvas:
    def __init__(self, parent_frame):
        self.canvas = tk.Canvas(parent_frame, bg="#1e1e1e")
        self.canvas.pack(fill="both", expand=True)

        self.images = []  # List of ImageTk references
        self.image_items = []  # List of canvas item IDs
        self.image_meta = {}  # Dict: canvas_item_id → full PIL image
        self.drag_data = {}  # Temporary drag state

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)

    def add_image(self, pil_image):
        full_img = pil_image.copy()

        # Resize proportionally (half the original size)
        scale_factor = 0.5
        thumb_width = int(full_img.width * scale_factor)
        thumb_height = int(full_img.height * scale_factor)
        thumb_img = full_img.resize(
            (thumb_width, thumb_height), Image.Resampling.LANCZOS
        )

        tk_img = ImageTk.PhotoImage(thumb_img)

        # Add to canvas
        x, y = 50, 50
        item_id = self.canvas.create_image(x, y, image=tk_img, anchor="nw")

        self.images.append(tk_img)
        self.image_items.append(item_id)
        self.image_meta[item_id] = full_img  # ✅ Dict instead of list

        # Right-click to delete
        self.canvas.tag_bind(
            item_id, "<Button-3>", lambda e, item=item_id: self.remove_image(item)
        )

    def remove_image(self, item_id):
        if item_id in self.image_items:
            index = self.image_items.index(item_id)
            self.canvas.delete(item_id)

            del self.image_items[index]
            del self.images[index]
            if item_id in self.image_meta:
                del self.image_meta[item_id]

    def on_press(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        self.drag_data["item"] = item
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_drag(self, event):
        item = self.drag_data.get("item")
        if item:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            self.canvas.move(item, dx, dy)
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def get_widget(self):
        return self.canvas

    def export_canvas_as_image(self, save_path=None):
        if not self.image_items:
            messagebox.showwarning("Empty", "No images to export.")
            return

        scale_factor = 0.5  # Matches scaling used in add_image()
        upscale_factor = 1.0  # You can adjust this to control final image size

        image_boxes = []

        for item_id in self.image_items:
            coords = self.canvas.coords(item_id)
            if not coords or item_id not in self.image_meta:
                continue

            thumb_x, thumb_y = map(int, coords)
            full_img = self.image_meta[item_id]

            # 1. Convert position to full image coordinates
            full_x = int(thumb_x / scale_factor)
            full_y = int(thumb_y / scale_factor)

            # 2. Resize full image (upscale)
            enlarged_img = full_img.resize(
                (
                    int(full_img.width * upscale_factor),
                    int(full_img.height * upscale_factor),
                ),
                Image.Resampling.LANCZOS,  # type: ignore
            )

            # 3. Adjust position for upscaled image
            adj_x = int(full_x * upscale_factor)
            adj_y = int(full_y * upscale_factor)

            image_boxes.append(
                (enlarged_img, adj_x, adj_y, enlarged_img.width, enlarged_img.height)
            )

        if not image_boxes:
            messagebox.showerror("Error", "No images found on canvas.")
            return

        # Compute bounding box
        min_x = min(x for _, x, y, w, h in image_boxes)
        min_y = min(y for _, x, y, w, h in image_boxes)
        max_x = max(x + w for _, x, y, w, h in image_boxes)
        max_y = max(y + h for _, x, y, w, h in image_boxes)

        export_width = max_x - min_x
        export_height = max_y - min_y

        # Create final canvas
        final_image = Image.new("RGB", (export_width, export_height), color=(0, 0, 0))

        for img, x, y, w, h in image_boxes:
            paste_x = x - min_x
            paste_y = y - min_y
            final_image.paste(img, (paste_x, paste_y))

        if not save_path:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png", filetypes=[("PNG Image", "*.png")]
            )

        if save_path:
            final_image.save(save_path)
            messagebox.showinfo("Exported", f"Image saved to:\n{save_path}")
