import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import pytesseract
import os
import csv
import shutil

class PageRenamerTrainer:
    def __init__(self, root):
        self.root = root
        self.root.title("Разметка номеров страниц (две области)")

        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.image_list = []
        self.current_index = 0
        self.image_path = None
        self.img = None
        self.tk_img = None

        self.start_x = self.start_y = self.end_x = self.end_y = None
        self.rects = []
        self.coords = []

        self.selecting_part = 0  # 0 — левая страница, 1 — правая

        self.canvas.bind("<ButtonPress-1>", self.on_start)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_drop)

        self.menu = tk.Menu(root)
        self.menu.add_command(label="Открыть папку", command=self.load_images_from_folder)
        self.menu.add_command(label="Следующее изображение", command=self.process_current_image)
        self.menu.add_command(label="Пропустить изображение", command=self.skip_current_image)  # Новая команда
        root.config(menu=self.menu)

        self.output_folder = "renamed_images"
        os.makedirs(self.output_folder, exist_ok=True)
        self.csv_file = "train_data.csv"
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "filename",
                    "left_coords", "left_ocr",
                    "right_coords", "right_ocr",
                    "final_name"
                ])

    # Новый метод для пропуска изображения
    def skip_current_image(self):
        self.current_index += 1
        self.show_image()

    def load_images_from_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку с изображениями")
        if not folder:
            return
        self.image_list = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg")) and not f.startswith("._")
        ]
        self.current_index = 0
        self.show_image()

    def show_image(self):
        if not self.image_list or self.current_index >= len(self.image_list):
            messagebox.showinfo("Готово", "Все изображения обработаны!")
            return
        self.image_path = self.image_list[self.current_index]
        self.img = Image.open(self.image_path)
        self.tk_img = ImageTk.PhotoImage(self.img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self.rects = []
        self.coords = []
        self.selecting_part = 0

    def on_start(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.selecting_part < 2:
            rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y, outline="red"
            )
            self.rects.append(rect)

    def on_drag(self, event):
        if self.selecting_part >= 2:
            return
        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)
        self.canvas.coords(
            self.rects[self.selecting_part],
            self.start_x, self.start_y, self.end_x, self.end_y
        )

    def on_drop(self, event):
        if self.selecting_part >= 2:
            return
        coords = (
            int(min(self.start_x, self.end_x)),
            int(min(self.start_y, self.end_y)),
            int(max(self.start_x, self.end_x)),
            int(max(self.start_y, self.end_y))
        )
        self.coords.append(coords)
        self.selecting_part += 1

    def process_current_image(self):
        if len(self.coords) < 2:
            messagebox.showwarning("Недостаточно областей", "Выделите две области: сначала левую, потом правую.")
            return

        left_crop = self.img.crop(self.coords[0])
        right_crop = self.img.crop(self.coords[1])

        left_text = pytesseract.image_to_string(left_crop, lang="rus+eng", config="--psm 6").strip()
        right_text = pytesseract.image_to_string(right_crop, lang="rus+eng", config="--psm 6").strip()

        suggested_name = f"{left_text}-{right_text}"

        final_name = simpledialog.askstring(
            "Введите итоговое имя файла",
            f"Левый: '{left_text}'\nПравый: '{right_text}'\n\nВведите имя (например: 12-13):",
            initialvalue=suggested_name
        )
        if not final_name:
            return

        ext = os.path.splitext(self.image_path)[1]
        new_filename = f"{final_name}{ext}"
        new_path = os.path.join(self.output_folder, new_filename)
        shutil.copy(self.image_path, new_path)

        # Закомментировано сохранение в CSV для пропуска
        # with open(self.csv_file, "a", newline="", encoding="utf-8") as f:
        #     writer = csv.writer(f)
        #     writer.writerow([
        #         os.path.basename(self.image_path),
        #         self.coords[0], left_text,
        #         self.coords[1], right_text,
        #         final_name
        #     ])

        self.current_index += 1
        self.show_image()

if __name__ == "__main__":
    root = tk.Tk()
    app = PageRenamerTrainer(root)
    root.mainloop()
