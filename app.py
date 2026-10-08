import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import sys
import json

try:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

CONFIG_PATH = os.path.join(APP_DIR, "config.json")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".bmp", ".webp")


def get_template_dir():
    for name in ("templates", "template"):
        path = os.path.join(APP_DIR, name)
        if os.path.isdir(path):
            return path
    return os.path.join(APP_DIR, "templates")


class TabelaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Εφαρμογή Δημιουργίας Ταμπελών A3")
        self.root.geometry("1100x750")

        # Φόρτωση αποθηκευμένων ρυθμίσεων
        self.config = self.load_config()
        self.templates_cfg = self.config.get("templates", {}) or {}

        # Μεταβλητές
        self.image_path = None
        self.export_path = self.config.get("export_path") or None
        self.orig_img = None
        self.preview_img = None
        self.tk_img = None
        self.scale = 1.0
        self.current_key = None

        # Προεπιλεγμένο χρώμα κειμένου
        self.text_color = tuple(self.config.get("text_color", [0, 0, 0]))

        # Δημιουργία φακέλων με το ίδιο όνομα με τις φωτογραφίες
        self.create_folders = tk.BooleanVar(value=bool(self.config.get("create_folders", False)))

        # Συντεταγμένες που έκανε κλικ ο χρήστης
        self.text_x = 0
        self.text_y = 0

        self.setup_ui()
        self.populate_templates()
        self.restore_last()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- Ρυθμίσεις ----------
    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_config(self):
        self.config["export_path"] = self.export_path or ""
        self.config["font_size"] = self.entry_font_size.get().strip()
        self.config["text_color"] = list(self.text_color)
        self.config["suffix"] = self.entry_suffix.get()
        self.config["last_template"] = self.current_key or ""
        self.config["create_folders"] = bool(self.create_folders.get())

        if self.current_key:
            self.templates_cfg[self.current_key] = {
                "text_x": self.text_x,
                "text_y": self.text_y,
                "font_size": self.entry_font_size.get().strip(),
                "text_color": list(self.text_color),
                "suffix": self.entry_suffix.get(),
            }

        self.config["templates"] = self.templates_cfg
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def on_close(self):
        self.save_config()
        self.root.destroy()

    # ---------- UI ----------
    def add_context_menu(self, widget):
        """Προσθέτει μενού με Δεξί Κλικ (Copy/Paste) σε όποιο κουτάκι το καλέσουμε"""
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Αποκοπή (Cut)", command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="Αντιγραφή (Copy)", command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="Επικόλληση (Paste)", command=lambda: widget.event_generate("<<Paste>>"))

        def show_menu(event):
            menu.tk_popup(event.x_root, event.y_root)

        widget.bind("<Button-3>", show_menu)

    def setup_ui(self):
        # --- Αριστερό Panel (Ρυθμίσεις) ---
        left_frame = tk.Frame(self.root, width=350, padx=15, pady=15)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left_frame, text="1. Επιλογή Template", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 5))

        self.combo_templates = ttk.Combobox(left_frame, state="readonly")
        self.combo_templates.pack(fill=tk.X, pady=2)
        self.combo_templates.bind("<<ComboboxSelected>>", self.on_template_selected)

        self.btn_refresh = ttk.Button(left_frame, text="Ανανέωση λίστας", command=self.populate_templates)
        self.btn_refresh.pack(fill=tk.X, pady=2)

        ttk.Label(left_frame, text="ή custom εικόνα:", font=("Arial", 8), foreground="gray").pack(anchor="w", pady=(8, 0))
        self.btn_import = ttk.Button(left_frame, text="Εισαγωγή Εικόνας (PNG/JPG)", command=self.load_image)
        self.btn_import.pack(fill=tk.X, pady=2)
        self.lbl_image = ttk.Label(left_frame, text="Δεν επιλέχθηκε εικόνα", foreground="gray")
        self.lbl_image.pack(anchor="w", pady=(0, 10))

        self.btn_export = ttk.Button(left_frame, text="Φάκελος Αποθήκευσης (Export)", command=self.set_export_dir)
        self.btn_export.pack(fill=tk.X, pady=2)
        self.lbl_export = ttk.Label(left_frame, text="Δεν επιλέχθηκε φάκελος", foreground="gray")
        self.lbl_export.pack(anchor="w", pady=(0, 15))

        ttk.Label(left_frame, text="2. Εισαγωγή Κωδικών", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 5))

        # Notebook (Tabs) για τους 2 τρόπους εισαγωγής
        self.tabs = ttk.Notebook(left_frame)
        self.tabs.pack(fill=tk.X, pady=5)

        # Tab 1: Με κόμμα
        tab_list = ttk.Frame(self.tabs)
        self.tabs.add(tab_list, text="Λίστα (με κόμμα)")
        ttk.Label(tab_list, text="π.χ. 1234, 5678, 1598").pack(anchor="w", padx=5, pady=2)
        self.entry_list = tk.Text(tab_list, height=4, width=30)
        self.entry_list.pack(padx=5, pady=5)
        self.add_context_menu(self.entry_list)  # Προσθήκη δεξί κλικ!

        # Tab 2: Από - Έως
        tab_range = ttk.Frame(self.tabs)
        self.tabs.add(tab_range, text="Από - Έως")
        range_frame = tk.Frame(tab_range)
        range_frame.pack(padx=5, pady=15)
        ttk.Label(range_frame, text="Από:").grid(row=0, column=0, padx=5)
        self.entry_from = ttk.Entry(range_frame, width=10)
        self.entry_from.grid(row=0, column=1, padx=5)
        self.add_context_menu(self.entry_from)  # Προσθήκη δεξί κλικ!

        ttk.Label(range_frame, text="Έως:").grid(row=0, column=2, padx=5)
        self.entry_to = ttk.Entry(range_frame, width=10)
        self.entry_to.grid(row=0, column=3, padx=5)
        self.add_context_menu(self.entry_to)  # Προσθήκη δεξί κλικ!

        ttk.Label(left_frame, text="3. Εμφάνιση & Ονομασία", font=("Arial", 12, "bold")).pack(anchor="w", pady=(15, 5))

        tk.Label(left_frame, text="Μέγεθος Γραμματοσειράς:").pack(anchor="w")
        self.entry_font_size = ttk.Entry(left_frame)
        self.entry_font_size.insert(0, str(self.config.get("font_size", "150")))
        self.entry_font_size.pack(fill=tk.X, pady=2)
        self.add_context_menu(self.entry_font_size)  # Προσθήκη δεξί κλικ!
        self.entry_font_size.bind("<KeyRelease>", lambda e: self.update_preview())
        self.entry_font_size.bind("<FocusOut>", lambda e: (self.save_config(), self.update_preview()))

        # Επιλογή Χρώματος
        color_frame = tk.Frame(left_frame)
        color_frame.pack(fill=tk.X, pady=10)
        tk.Label(color_frame, text="Χρώμα Κωδικού:").pack(side=tk.LEFT)
        color_hex = "#%02x%02x%02x" % self.text_color
        self.btn_color = tk.Button(color_frame, bg=color_hex, width=6, relief="ridge", command=self.choose_color)
        self.btn_color.pack(side=tk.LEFT, padx=10)

        tk.Label(left_frame, text="Πρόσθετο κείμενο στο όνομα (προαιρετικό):").pack(anchor="w", pady=(5, 0))
        tk.Label(left_frame, text="π.χ. '_A3' -> '1234_A3.jpg'", font=("Arial", 8), fg="gray").pack(anchor="w")
        self.entry_suffix = ttk.Entry(left_frame)
        self.entry_suffix.insert(0, str(self.config.get("suffix", "")))
        self.entry_suffix.pack(fill=tk.X, pady=2)
        self.add_context_menu(self.entry_suffix)  # Προσθήκη δεξί κλικ!
        self.entry_suffix.bind("<FocusOut>", lambda e: self.save_config())

        # Checkbox: Δημιουργία άδειων φακέλων με ίδιο όνομα
        self.chk_folders = ttk.Checkbutton(
            left_frame,
            text="Δημιουργία άδειου φακέλου για κάθε φωτογραφία",
            variable=self.create_folders,
            command=self.save_config,
        )
        self.chk_folders.pack(anchor="w", pady=(10, 0))

        # Κουμπί Εκτέλεσης
        self.btn_generate = tk.Button(left_frame, text="ΔΗΜΙΟΥΡΓΙΑ ΑΡΧΕΙΩΝ", font=("Arial", 14, "bold"), bg="#4CAF50", fg="white", command=self.generate_images)
        self.btn_generate.pack(fill=tk.X, pady=25, ipady=10)

        # --- Δεξί Panel (Προεπισκόπηση) ---
        right_frame = tk.Frame(self.root, bg="#e0e0e0")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Label(right_frame, text="Κάνε ΚΛΙΚ πάνω στην εικόνα για να ορίσεις πού θα μπει ο κωδικός", font=("Arial", 11), background="#e0e0e0").pack(pady=10)

        self.canvas = tk.Canvas(right_frame, bg="white", cursor="crosshair")
        self.canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Εμφάνιση αποθηκευμένου φακέλου εξαγωγής
        if self.export_path and os.path.isdir(self.export_path):
            self.lbl_export.config(text=self.export_path, foreground="black")

    # ---------- Templates ----------
    def populate_templates(self):
        template_dir = get_template_dir()
        names = []
        if os.path.isdir(template_dir):
            for f in sorted(os.listdir(template_dir)):
                if f.lower().endswith(IMAGE_EXT):
                    names.append(f)
        self.combo_templates["values"] = names
        if not names:
            self.lbl_image.config(text="Δεν βρέθηκαν templates στον φάκελο", foreground="gray")

    def on_template_selected(self, event=None):
        name = self.combo_templates.get()
        if not name:
            return
        path = os.path.join(get_template_dir(), name)
        if os.path.exists(path):
            self.load_base_image(path)
            self.save_config()

    def restore_last(self):
        last = self.config.get("last_template") or ""
        values = list(self.combo_templates["values"])
        if last and last in values:
            self.combo_templates.set(last)
            self.on_template_selected()

    # ---------- Φόρτωση Εικόνας ----------
    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.webp")])
        if file_path:
            self.load_base_image(file_path)

    def load_base_image(self, file_path):
        self.image_path = file_path
        self.current_key = os.path.basename(file_path)
        self.lbl_image.config(text=self.current_key, foreground="black")
        self.orig_img = Image.open(file_path).convert("RGB")
        self.apply_settings(self.current_key)
        self.update_preview()

    def apply_settings(self, key):
        cfg = self.templates_cfg.get(key, {})
        font_size = cfg.get("font_size", self.config.get("font_size", "150"))
        color = tuple(cfg.get("text_color", self.config.get("text_color", [0, 0, 0])))
        suffix = cfg.get("suffix", self.config.get("suffix", ""))

        self.text_x = cfg.get("text_x", self.orig_img.width // 2)
        self.text_y = cfg.get("text_y", self.orig_img.height // 2)

        self.entry_font_size.delete(0, tk.END)
        self.entry_font_size.insert(0, str(font_size))
        self.entry_suffix.delete(0, tk.END)
        self.entry_suffix.insert(0, suffix)
        self.text_color = color
        self.btn_color.config(bg="#%02x%02x%02x" % color)

    # ---------- Ρυθμίσεις Εξαγωγής ----------
    def set_export_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.export_path = dir_path
            self.lbl_export.config(text=dir_path, foreground="black")
            self.save_config()

    def choose_color(self):
        color_code = colorchooser.askcolor(title="Επιλογή Χρώματος", initialcolor=self.text_color)
        if color_code[0]:
            self.text_color = tuple(map(int, color_code[0]))
            self.btn_color.config(bg=color_code[1])
            self.save_config()
            self.update_preview()

    # ---------- Σχεδίαση ----------
    @staticmethod
    def draw_centered(draw, center, text, font, fill):
        """Σχεδιάζει το κείμενο κεντραρισμένο γύρω από το σημείο center."""
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = center[0] - w / 2 - bbox[0]
        y = center[1] - h / 2 - bbox[1]
        draw.text((x, y), text, font=font, fill=fill)

    def get_font(self, size):
        try:
            return ImageFont.truetype("arialbd.ttf", size)
        except Exception:
            try:
                return ImageFont.truetype("arial.ttf", size)
            except Exception:
                return ImageFont.load_default()

    def update_preview(self):
        if not self.orig_img:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width < 100: canvas_width = 700
        if canvas_height < 100: canvas_height = 500

        scale_w = canvas_width / self.orig_img.width
        scale_h = canvas_height / self.orig_img.height
        self.scale = min(scale_w, scale_h)

        new_w = int(self.orig_img.width * self.scale)
        new_h = int(self.orig_img.height * self.scale)

        temp_img = self.orig_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(temp_img)

        preview_x = self.text_x * self.scale
        preview_y = self.text_y * self.scale
        preview_font_size = max(1, int(float(self.entry_font_size.get() or 150) * self.scale))

        font = self.get_font(preview_font_size)
        self.draw_centered(draw, (preview_x, preview_y), "0000", font, self.text_color)

        self.tk_img = ImageTk.PhotoImage(temp_img)
        self.canvas.delete("all")
        self.canvas.create_image(canvas_width // 2, canvas_height // 2, anchor="center", image=self.tk_img)

    def on_canvas_click(self, event):
        if not self.orig_img:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        img_w = self.orig_img.width * self.scale
        img_h = self.orig_img.height * self.scale
        offset_x = (canvas_width - img_w) / 2
        offset_y = (canvas_height - img_h) / 2

        if event.x < offset_x or event.x > offset_x + img_w or event.y < offset_y or event.y > offset_y + img_h:
            return

        self.text_x = int((event.x - offset_x) / self.scale)
        self.text_y = int((event.y - offset_y) / self.scale)

        self.save_config()
        self.update_preview()

    # ---------- Παραγωγή ----------
    def generate_images(self):
        if not self.image_path or not self.export_path:
            messagebox.showerror("Σφάλμα", "Πρέπει να επιλέξεις Εικόνα (Template/Import) και Φάκελο Αποθήκευσης (Export).")
            return

        codes = []
        current_tab = self.tabs.index("current")

        if current_tab == 0:
            raw_text = self.entry_list.get("1.0", tk.END).strip()
            if raw_text:
                codes = [c.strip() for c in raw_text.split(",") if c.strip()]
        else:
            raw_from = self.entry_from.get().strip()
            raw_to = self.entry_to.get().strip()
            try:
                start = int(raw_from)
                end = int(raw_to)
                width = max(len(raw_from), len(raw_to))
                codes = [str(i).zfill(width) for i in range(start, end + 1)]
            except ValueError:
                messagebox.showerror("Σφάλμα", "Στο 'Από - Έως' πρέπει να βάλεις μόνο αριθμούς.")
                return

        if not codes:
            messagebox.showwarning("Προσοχή", "Δεν βρέθηκαν κωδικοί προς δημιουργία.")
            return

        suffix = self.entry_suffix.get().strip()
        try:
            font_size = int(self.entry_font_size.get())
        except Exception:
            font_size = 150

        font = self.get_font(font_size)
        make_folders = self.create_folders.get()
        self.save_config()

        try:
            for code in codes:
                img = self.orig_img.copy()
                draw = ImageDraw.Draw(img)

                self.draw_centered(draw, (self.text_x, self.text_y), code, font, self.text_color)

                filename = f"{code}{suffix}.jpg"
                save_path = os.path.join(self.export_path, filename)

                img.save(save_path, "JPEG", quality=95, dpi=(300, 300))

                if make_folders:
                    folder_name = os.path.splitext(filename)[0]
                    os.makedirs(os.path.join(self.export_path, folder_name), exist_ok=True)

            messagebox.showinfo("Επιτυχία!", f"Δημιουργήθηκαν επιτυχώς {len(codes)} ταμπέλες στον φάκελο:\n{self.export_path}")

        except Exception as e:
            messagebox.showerror("Σφάλμα κατά την παραγωγή", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = TabelaApp(root)
    root.update()
    root.mainloop()
