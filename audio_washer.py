import os
import sys
import threading
import subprocess
import re
import json

# ==========================
# FFmpeg Setup
# ==========================
def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

base_path   = get_base_path()
ffmpeg_path = os.path.join(base_path, "ffmpeg")
os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")

import tkinter as tk
from tkinter import filedialog, ttk, messagebox

FFMPEG_EXE             = os.path.join(ffmpeg_path, "ffmpeg.exe")
FFPROBE_EXE           = os.path.join(ffmpeg_path, "ffprobe.exe")

SETTINGS_DIR = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "MediaForge",
)
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")


# ==========================
# THEME COLOURS
# ==========================
BG       = "#0e0e14"
CARD     = "#16161f"
PANEL    = "#1c1c28"
ACCENT   = "#7c5cfc"   # purple  — audio
ACCENT2  = "#fc5c7d"   # pink    — video
ACCENT3  = "#4ecca3"   # teal    — image
FG       = "#e8e8f0"
MUTED    = "#55556a"
ENTRY_BG = "#0a0a12"
SUCCESS  = "#4ecca3"
WARNING  = "#fcbe5c"
ERROR    = "#fc5c5c"
BORDER   = "#2a2a3a"


# ==========================
# FORMAT DEFINITIONS
# ==========================
AUDIO_INPUT_EXTS = [
    ".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".opus", ".wma",
    ".aiff", ".aif", ".alac", ".ac3", ".amr", ".ape", ".au", ".mka",
    ".mp2", ".ra", ".weba",
]

VIDEO_INPUT_EXTS = [
    ".mp4", ".m4v", ".mkv", ".webm", ".avi", ".mov", ".flv", ".wmv",
    ".mpeg", ".mpg", ".3gp", ".3g2", ".ts", ".mts", ".m2ts", ".ogv",
    ".vob", ".asf", ".rm", ".rmvb",
]

IMAGE_INPUT_EXTS = [
    ".jpg", ".jpeg", ".png", ".webp", ".avif", ".heic", ".heif", ".bmp",
    ".tiff", ".tif", ".gif", ".ico", ".tga", ".dds", ".ppm", ".pgm",
    ".pbm", ".pam", ".exr", ".jxl",
]

AUDIO_OUTPUTS = [
    ("MP3", ".mp3"),
    ("WAV", ".wav"),
    ("FLAC", ".flac"),
    ("AAC", ".aac"),
    ("M4A", ".m4a"),
    ("OGG", ".ogg"),
    ("OPUS", ".opus"),
    ("WMA", ".wma"),
    ("AIFF", ".aiff"),
    ("AC3", ".ac3"),
]

VIDEO_OUTPUTS = [
    ("MP4", ".mp4"),
    ("MKV", ".mkv"),
    ("WEBM", ".webm"),
    ("AVI", ".avi"),
    ("MOV", ".mov"),
    ("M4V", ".m4v"),
    ("GIF", ".gif"),
    ("MP3", ".mp3"),
    ("WAV", ".wav"),
]

IMAGE_OUTPUTS = [
    ("PNG", ".png"),
    ("JPG", ".jpg"),
    ("WEBP", ".webp"),
    ("AVIF", ".avif"),
    ("BMP", ".bmp"),
    ("TIFF", ".tiff"),
    ("GIF", ".gif"),
    ("ICO", ".ico"),
    ("TGA", ".tga"),
]

DOC_INPUT_EXTS = [
    ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".csv", ".json", ".xml",
    ".txt", ".html", ".htm", ".epub", ".zip"
]

DOC_OUTPUTS = [
    ("Markdown (.md)", ".md"),
]


def build_format_menu(src_label, ext_in, outputs, media_type):
    return {
        f"ANY {src_label:<5} -> {out_label}": {
            "ext_in": ext_in,
            "ext_out": ext_out,
            "type": media_type,
        }
        for out_label, ext_out in outputs
    }


MODES = {
    "AUDIO": {
        "color": ACCENT,
        "icon":  "♪",
        "formats": build_format_menu(
            "AUDIO", AUDIO_INPUT_EXTS, AUDIO_OUTPUTS, "audio"
        ),
    },
    "VIDEO": {
        "color": ACCENT2,
        "icon":  "▶",
        "formats": build_format_menu(
            "VIDEO", VIDEO_INPUT_EXTS, VIDEO_OUTPUTS, "video"
        ),
    },
    "IMAGE": {
        "color": ACCENT3,
        "icon":  "◈",
        "formats": build_format_menu(
            "IMAGE", IMAGE_INPUT_EXTS, IMAGE_OUTPUTS, "image"
        ),
    },
    "DOCUMENT": {
        "color": "#ff9f43",
        "icon":  "▤",
        "formats": build_format_menu(
            "DOCUMENT", DOC_INPUT_EXTS, DOC_OUTPUTS, "document"
        ),
    },
}

INPUT_EXTS_BY_CATEGORY = {
    "AUDIO": set(AUDIO_INPUT_EXTS),
    "VIDEO": set(VIDEO_INPUT_EXTS),
    "IMAGE": set(IMAGE_INPUT_EXTS),
    "DOCUMENT": set(DOC_INPUT_EXTS),
}

ALL_INPUT_EXTS = sorted(
    set(AUDIO_INPUT_EXTS) | set(VIDEO_INPUT_EXTS) | set(IMAGE_INPUT_EXTS) | set(DOC_INPUT_EXTS)
)

AUDIO_QUALITY = {
    "24-bit WAV  (best)":   ["-acodec", "pcm_s24le"],
    "16-bit WAV  (CD)":     ["-acodec", "pcm_s16le"],
    "MP3  320 kbps":        ["-b:a", "320k"],
    "MP3  192 kbps":        ["-b:a", "192k"],
    "MP3  128 kbps":        ["-b:a", "128k"],
    "FLAC (lossless)":      ["-acodec", "flac"],
    "AAC  256 kbps":        ["-b:a", "256k"],
    "OGG  320 kbps":        ["-b:a", "320k"],
}


# ==========================
# CONVERSION ENGINE
# ==========================
def _quality_bitrate(quality_params, default="320k"):
    if "-b:a" in quality_params:
        idx = quality_params.index("-b:a")
        if idx + 1 < len(quality_params):
            return quality_params[idx + 1]
    return default


def _run_ffmpeg(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-400:])


def _unique_output_path(path):
    if not os.path.exists(path):
        return path

    folder, filename = os.path.split(path)
    stem, ext = os.path.splitext(filename)
    n = 1
    while True:
        candidate = os.path.join(folder, f"{stem}_{n}{ext}")
        if not os.path.exists(candidate):
            return candidate
        n += 1


def convert_file(file_path, output_folder, fmt_info, quality_params):
    filename    = os.path.basename(file_path)
    name_no_ext = os.path.splitext(filename)[0]
    ext_out     = fmt_info["ext_out"]
    output_path = _unique_output_path(
        os.path.join(output_folder, name_no_ext + ext_out)
    )
    ftype       = fmt_info["type"]

    # ---- AUDIO via ffmpeg ----
    if ftype == "audio":
        bitrate = _quality_bitrate(quality_params)
        cmd = [FFMPEG_EXE, "-y", "-i", file_path, "-vn"]

        if ext_out == ".wav":
            codec = "pcm_s24le"
            if "-acodec" in quality_params:
                idx = quality_params.index("-acodec")
                if idx + 1 < len(quality_params):
                    codec = quality_params[idx + 1]
            cmd += ["-acodec", codec]
        elif ext_out == ".mp3":
            cmd += ["-codec:a", "libmp3lame", "-b:a", bitrate]
        elif ext_out == ".flac":
            cmd += ["-codec:a", "flac"]
        elif ext_out in (".aac", ".m4a"):
            cmd += ["-codec:a", "aac", "-b:a", _quality_bitrate(quality_params, "256k")]
        elif ext_out == ".ogg":
            cmd += ["-codec:a", "libvorbis", "-b:a", bitrate]
        elif ext_out == ".opus":
            cmd += ["-codec:a", "libopus", "-b:a", _quality_bitrate(quality_params, "160k")]
        elif ext_out == ".wma":
            cmd += ["-codec:a", "wmav2", "-b:a", _quality_bitrate(quality_params, "192k")]
        elif ext_out == ".aiff":
            cmd += ["-codec:a", "pcm_s16be"]
        elif ext_out == ".ac3":
            cmd += ["-codec:a", "ac3", "-b:a", _quality_bitrate(quality_params, "448k")]
        else:
            cmd += ["-codec:a", "copy"]

        cmd.append(output_path)
        _run_ffmpeg(cmd)
        return True, name_no_ext + ext_out

    # ---- VIDEO via ffmpeg ----
    elif ftype == "video":
        if ext_out == ".gif":
            cmd = [FFMPEG_EXE, "-y", "-i", file_path,
                   "-vf", "fps=10,scale=480:-1:flags=lanczos",
                   "-loop", "0", output_path]
        elif ext_out == ".mp3":
            cmd = [FFMPEG_EXE, "-y", "-i", file_path,
                   "-vn", "-b:a", "320k", output_path]
        elif ext_out == ".wav":
            cmd = [FFMPEG_EXE, "-y", "-i", file_path,
                   "-vn", "-acodec", "pcm_s16le", output_path]
        elif ext_out == ".mp4":
            cmd = [FFMPEG_EXE, "-y", "-i", file_path,
                   "-c:v", "libx264", "-crf", "23",
                   "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
                   "-movflags", "+faststart", output_path]
        elif ext_out == ".m4v":
            cmd = [FFMPEG_EXE, "-y", "-i", file_path,
                   "-c:v", "libx264", "-crf", "23",
                   "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
                   output_path]
        elif ext_out == ".mov":
            cmd = [FFMPEG_EXE, "-y", "-i", file_path,
                   "-c:v", "libx264", "-crf", "23",
                   "-preset", "medium", "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-b:a", "192k", output_path]
        elif ext_out == ".webm":
            cmd = [FFMPEG_EXE, "-y", "-i", file_path,
                   "-c:v", "libvpx-vp9", "-crf", "30",
                   "-b:v", "0", "-c:a", "libopus", output_path]
        elif ext_out == ".mkv":
            cmd = [FFMPEG_EXE, "-y", "-i", file_path,
                   "-c:v", "libx264", "-crf", "23",
                   "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
                   output_path]
        elif ext_out == ".avi":
            cmd = [FFMPEG_EXE, "-y", "-i", file_path,
                   "-c:v", "libxvid", "-c:a", "mp3", output_path]
        else:
            cmd = [FFMPEG_EXE, "-y", "-i", file_path,
                   "-c:v", "copy", "-c:a", "copy", output_path]

        _run_ffmpeg(cmd)
        return True, name_no_ext + ext_out

    # ---- IMAGE via ffmpeg ----
    elif ftype == "image":
        cmd = [FFMPEG_EXE, "-y", "-i", file_path, "-frames:v", "1"]
        if ext_out in (".jpg", ".jpeg"):
            cmd += ["-q:v", "2"]
        elif ext_out == ".webp":
            cmd += ["-quality", "90", "-compression_level", "6"]
        elif ext_out == ".avif":
            cmd += ["-crf", "23", "-still-picture", "1"]
        elif ext_out == ".ico":
            cmd += ["-vf", "scale=256:256:force_original_aspect_ratio=decrease"]

        cmd.append(output_path)
        _run_ffmpeg(cmd)
        return True, name_no_ext + ext_out

    # ---- DOCUMENT via markitdown ----
    elif ftype == "document":
        from markitdown import MarkItDown
        md_converter = MarkItDown()
        result = md_converter.convert(file_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.text_content)
        return True, name_no_ext + ext_out

    raise RuntimeError("Unknown conversion type")


# ==========================
# DRAG & DROP HELPER
# ==========================
def enable_dnd(widget, callback):
    try:
        from tkinterdnd2 import DND_FILES

        def register(target):
            target.drop_target_register(DND_FILES)
            target.dnd_bind("<<Drop>>", lambda e: callback(_parse_drop(e.data)))
            for child in target.winfo_children():
                register(child)

        register(widget)
        return True
    except Exception:
        return False


def _parse_drop(raw):
    return [m[0] or m[1] for m in re.findall(r'\{([^}]+)\}|(\S+)', raw)]


def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(data):
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


# ==========================
# MAIN APPLICATION
# ==========================
class MediaForge(tk.Frame):

    def __init__(self, root):
        super().__init__(root, bg=BG)
        self.settings = load_settings()
        self.root = root
        self.root.title("MediaForge — Universal Converter")
        self.root.geometry(self.settings.get("geometry", "820x700"))
        self.root.minsize(720, 600)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.pack(fill="both", expand=True)

        self.queued_files   = []
        self.output_folder  = tk.StringVar(
            value=self.settings.get("output_folder", "")
        )
        self.selected_cat   = tk.StringVar(
            value=self.settings.get("selected_cat", "AUDIO")
        )
        self.fmt_var        = tk.StringVar()
        self.quality_var    = tk.StringVar(
            value=self.settings.get("quality", "24-bit WAV  (best)")
        )
        self.same_folder    = tk.BooleanVar(
            value=self.settings.get("same_folder", False)
        )
        self.last_formats   = self.settings.get("formats", {})
        self.is_running     = False
        self.dnd_ok         = False

        self._build()
        self._switch_cat(self.selected_cat.get())
        if self.same_folder.get():
            self._toggle_same()
        self._check_dependencies()

    # ──────────────────────────────────────────────
    # BUILD UI
    # ──────────────────────────────────────────────
    def _build(self):
        self._build_titlebar()
        self._build_tabs()
        self._build_body()
        self._build_statusbar()

    # ---- Title bar ----
    def _build_titlebar(self):
        bar = tk.Frame(self, bg=CARD, height=58)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="MediaForge",
                 font=("Consolas", 18, "bold"),
                 bg=CARD, fg=ACCENT).pack(side="left", padx=22, pady=10)
        tk.Label(bar, text="Universal File Converter",
                 font=("Consolas", 9), bg=CARD, fg=MUTED).pack(side="left")
        tk.Label(bar, text=" v2.0 ",
                 font=("Consolas", 8, "bold"),
                 bg=ACCENT, fg=FG, padx=6, pady=2).pack(side="right", padx=18)

    # ---- Category tabs ----
    def _build_tabs(self):
        bar = tk.Frame(self, bg=BG, pady=10)
        bar.pack(fill="x", padx=18)
        self.cat_btns = {}
        for cat, info in MODES.items():
            btn = tk.Button(bar,
                            text=f"  {info['icon']}  {cat}  ",
                            font=("Consolas", 9, "bold"),
                            bg=PANEL, fg=MUTED,
                            relief="flat", cursor="hand2",
                            padx=12, pady=8,
                            command=lambda c=cat: self._switch_cat(c))
            btn.pack(side="left", padx=(0, 6))
            self.cat_btns[cat] = btn

    # ---- Main body ----
    def _build_body(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=(0, 6))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=5)
        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)

    # ---- Left config panel ----
    def _build_left(self, parent):
        left = tk.Frame(parent, bg=PANEL, padx=18, pady=18)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Format selector
        self._lbl(left, "CONVERSION FORMAT")
        self.fmt_var = tk.StringVar()
        self.fmt_menu = tk.OptionMenu(left, self.fmt_var, "")
        self._style_option(self.fmt_menu)
        self.fmt_menu.pack(fill="x", pady=(0, 14))

        # Quality selector
        self._lbl(left, "AUDIO QUALITY")
        self.qual_menu = tk.OptionMenu(left, self.quality_var,
                                       *list(AUDIO_QUALITY.keys()))
        self._style_option(self.qual_menu)
        self.qual_menu.pack(fill="x", pady=(0, 14))

        # Output folder
        self._lbl(left, "OUTPUT FOLDER")
        out_row = tk.Frame(left, bg=PANEL)
        out_row.pack(fill="x")
        self.out_entry = tk.Entry(out_row, textvariable=self.output_folder,
                                  font=("Consolas", 8),
                                  bg=ENTRY_BG, fg=FG,
                                  insertbackground=FG,
                                  relief="flat", bd=0,
                                  highlightthickness=1,
                                  highlightbackground=BORDER,
                                  highlightcolor=ACCENT)
        self.out_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 6))
        self._mk_btn(out_row, "…", self._browse_output,
                     ACCENT, FG, width=3).pack(side="right")

        tk.Checkbutton(left, text="Save next to source files",
                       variable=self.same_folder,
                       font=("Consolas", 8), bg=PANEL, fg=MUTED,
                       selectcolor=ENTRY_BG,
                       activebackground=PANEL, activeforeground=FG,
                       command=self._toggle_same).pack(anchor="w", pady=(5, 18))

        # Convert button
        self.convert_btn = tk.Button(left,
                                     text="▶   CONVERT",
                                     font=("Consolas", 11, "bold"),
                                     bg=ACCENT, fg=FG,
                                     relief="flat", cursor="hand2",
                                     pady=13,
                                     command=self._start)
        self.convert_btn.pack(fill="x")

        self._mk_btn(left, "✕  Clear Queue", self._clear_queue,
                     PANEL, MUTED).pack(fill="x", pady=(8, 0))

        self.count_lbl = tk.Label(left, text="0 files queued",
                                  font=("Consolas", 8),
                                  bg=PANEL, fg=MUTED)
        self.count_lbl.pack(pady=(10, 0))

    # ---- Right panel (drop zone + log) ----
    def _build_right(self, parent):
        right = tk.Frame(parent, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=3)
        right.rowconfigure(2, weight=4)
        right.columnconfigure(0, weight=1)

        # Drop zone
        self.drop_frame = tk.Frame(right, bg=PANEL,
                                   highlightthickness=2,
                                   highlightbackground=BORDER)
        self.drop_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 0))

        inner = tk.Frame(self.drop_frame, bg=PANEL)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        self.drop_icon = tk.Label(inner, text="⊕",
                                  font=("Consolas", 42),
                                  bg=PANEL, fg=BORDER)
        self.drop_icon.pack()
        self.drop_hint = tk.Label(inner,
                                  text="Drop files / folders here",
                                  font=("Consolas", 10, "bold"),
                                  bg=PANEL, fg=MUTED)
        self.drop_hint.pack(pady=(4, 2))
        self.drop_sub = tk.Label(inner,
                                 text="or click to browse",
                                 font=("Consolas", 8),
                                 bg=PANEL, fg=MUTED)
        self.drop_sub.pack()

        # Click to browse on entire drop zone
        for w in (self.drop_frame, inner, self.drop_icon,
                  self.drop_hint, self.drop_sub):
            w.bind("<Button-1>", lambda e: self._browse_files())
            w.bind("<Enter>",    lambda e: self._drop_hover(True))
            w.bind("<Leave>",    lambda e: self._drop_hover(False))

        # Drag & drop
        self.dnd_ok = enable_dnd(self.drop_frame, self._add_files)
        if not self.dnd_ok:
            self.drop_sub.config(
                text="or click to browse  (install tkinterdnd2 for drag & drop)")

        # Progress bar
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("MF.Horizontal.TProgressbar",
                        troughcolor=ENTRY_BG, background=ACCENT,
                        bordercolor=ENTRY_BG,
                        lightcolor=ACCENT, darkcolor=ACCENT)
        self.progress = ttk.Progressbar(right, mode="determinate",
                                        style="MF.Horizontal.TProgressbar")
        self.progress.grid(row=1, column=0, sticky="ew", pady=6)

        # Log box
        log_wrap = tk.Frame(right, bg=ENTRY_BG,
                            highlightthickness=1,
                            highlightbackground=BORDER)
        log_wrap.grid(row=2, column=0, sticky="nsew")

        self.log_box = tk.Text(log_wrap,
                               font=("Consolas", 8),
                               bg=ENTRY_BG, fg=FG,
                               insertbackground=FG,
                               relief="flat", bd=4,
                               state="disabled", wrap="word")
        self.log_box.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(log_wrap, command=self.log_box.yview,
                          bg=PANEL, troughcolor=ENTRY_BG, relief="flat")
        sb.pack(side="right", fill="y")
        self.log_box.configure(yscrollcommand=sb.set)

        self.log_box.tag_configure("ok",   foreground=SUCCESS)
        self.log_box.tag_configure("err",  foreground=ERROR)
        self.log_box.tag_configure("info", foreground=MUTED)
        self.log_box.tag_configure("warn", foreground=WARNING)
        self.log_box.tag_configure("hdr",  foreground=ACCENT)

    # ---- Status bar ----
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=CARD, height=26)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status_lbl = tk.Label(bar, text="Ready",
                                   font=("Consolas", 8),
                                   bg=CARD, fg=MUTED)
        self.status_lbl.pack(side="left", padx=14)

        dnd_txt   = "Drag & Drop: ON" if self.dnd_ok else "Drag & Drop: OFF  →  pip install tkinterdnd2"
        dnd_color = SUCCESS if self.dnd_ok else WARNING
        tk.Label(bar, text=dnd_txt,
                 font=("Consolas", 8),
                 bg=CARD, fg=dnd_color).pack(side="right", padx=14)

    # ──────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────
    def _lbl(self, parent, text):
        tk.Label(parent, text=text,
                 font=("Consolas", 7, "bold"),
                 bg=PANEL, fg=MUTED).pack(anchor="w", pady=(10, 3))

    def _mk_btn(self, parent, text, cmd, bg, fg, width=None):
        kw = dict(font=("Consolas", 8), bg=bg, fg=fg,
                  relief="flat", cursor="hand2",
                  command=cmd, padx=10, pady=6)
        if width:
            kw["width"] = width
        return tk.Button(parent, text=text, **kw)

    def _style_option(self, menu):
        menu.config(font=("Consolas", 8),
                    bg=ENTRY_BG, fg=FG,
                    activebackground=ACCENT, activeforeground=FG,
                    highlightthickness=0, relief="flat", bd=0)
        menu["menu"].config(font=("Consolas", 8),
                            bg=ENTRY_BG, fg=FG,
                            activebackground=ACCENT, activeforeground=FG,
                            relief="flat")

    # ──────────────────────────────────────────────
    # CATEGORY / FORMAT SWITCHING
    # ──────────────────────────────────────────────
    def _switch_cat(self, cat):
        prev_cat = self.selected_cat.get()
        prev_fmt = self.fmt_var.get()
        if prev_fmt:
            self.last_formats[prev_cat] = prev_fmt

        if cat not in MODES:
            cat = "AUDIO"

        self.selected_cat.set(cat)
        info  = MODES[cat]
        color = info["color"]

        # Highlight active tab
        for c, btn in self.cat_btns.items():
            btn.config(bg=MODES[c]["color"] if c == cat else PANEL,
                       fg=FG if c == cat else MUTED)

        # Rebuild format menu
        fmts = list(info["formats"].keys())
        menu = self.fmt_menu["menu"]
        menu.delete(0, "end")
        for f in fmts:
            menu.add_command(label=f,
                             command=lambda v=f: self.fmt_var.set(v))
        saved_fmt = self.last_formats.get(cat)
        self.fmt_var.set(saved_fmt if saved_fmt in fmts else fmts[0])

        # Quality only relevant for audio
        state = "normal" if cat == "AUDIO" else "disabled"
        self.qual_menu.config(state=state)

        # Accent drop zone border & icon with category colour
        self.drop_frame.config(highlightbackground=color)
        self.drop_icon.config(fg=color)
        self.convert_btn.config(bg=color)

        # Update progress bar colour
        style = ttk.Style()
        style.configure("MF.Horizontal.TProgressbar", background=color,
                        lightcolor=color, darkcolor=color)

    # ──────────────────────────────────────────────
    # DROP ZONE HOVER
    # ──────────────────────────────────────────────
    def _drop_hover(self, entering):
        cat   = self.selected_cat.get()
        color = MODES[cat]["color"] if entering else BORDER
        self.drop_frame.config(highlightbackground=color)

    # ──────────────────────────────────────────────
    # FILE QUEUE
    # ──────────────────────────────────────────────
    def _category_for_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        for cat, exts in INPUT_EXTS_BY_CATEGORY.items():
            if ext in exts:
                return cat
        return None

    def _expand_paths(self, paths):
        files = []
        for p in paths:
            p = p.strip().strip("{}")
            if os.path.isdir(p):
                for root, _, names in os.walk(p):
                    for name in names:
                        files.append(os.path.join(root, name))
            elif os.path.isfile(p):
                files.append(p)
        return files

    def _add_files(self, paths):
        files = self._expand_paths(paths)
        detected = [(p, self._category_for_file(p)) for p in files]
        supported = [(p, cat) for p, cat in detected if cat]
        unsupported = len(detected) - len(supported)

        if not supported:
            self._log("No supported media files found.", "warn")
            return

        cat = self.selected_cat.get()
        if not any(file_cat == cat for _, file_cat in supported):
            cat = supported[0][1]
            self._switch_cat(cat)
            self._log(f"Switched to {cat} for dropped files.", "info")

        added = 0
        skipped_category = 0
        skipped_duplicate = 0
        for p, file_cat in supported:
            if file_cat != cat:
                skipped_category += 1
                continue
            if p in self.queued_files:
                skipped_duplicate += 1
                continue
            self.queued_files.append(p)
            added += 1

        self._update_count()
        if added:
            self._log(f"+ {added} file(s) added to queue", "info")
        if skipped_category:
            self._log(f"{skipped_category} file(s) skipped from other categories.", "warn")
        if skipped_duplicate:
            self._log(f"{skipped_duplicate} duplicate file(s) skipped.", "warn")
        if unsupported:
            self._log(f"{unsupported} unsupported file(s) skipped.", "warn")

    def _browse_files(self):
        cat    = self.selected_cat.get()
        exts  = sorted(INPUT_EXTS_BY_CATEGORY[cat])
        types = [(f"{cat.title()} files", " ".join(f"*{e}" for e in exts)),
                 ("All supported media", " ".join(f"*{e}" for e in ALL_INPUT_EXTS)),
                 ("All files", "*.*")]
        paths = filedialog.askopenfilenames(title="Select files", filetypes=types)
        if paths:
            self._add_files(list(paths))

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.output_folder.set(path)
            self.same_folder.set(False)

    def _toggle_same(self):
        if self.same_folder.get():
            self.output_folder.set("<same as source>")
            self.out_entry.config(state="disabled")
        else:
            self.output_folder.set("")
            self.out_entry.config(state="normal")

    def _clear_queue(self):
        self.queued_files.clear()
        self._update_count()
        self._log("Queue cleared.", "info")

    def _update_count(self):
        n = len(self.queued_files)
        self.count_lbl.config(text=f"{n} file{'s' if n != 1 else ''} queued")

    # ──────────────────────────────────────────────
    # LOGGING
    # ──────────────────────────────────────────────
    def _log(self, msg, tag=""):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_status(self, msg):
        self.status_lbl.config(text=msg)

    def _check_dependencies(self):
        missing = [
            path for path in (FFMPEG_EXE, FFPROBE_EXE)
            if not os.path.exists(path)
        ]
        if not missing:
            self._log("FFmpeg ready.", "ok")
            return

        msg = "Missing FFmpeg files:\n" + "\n".join(missing)
        self._log(msg, "err")
        self._set_status("FFmpeg missing")
        messagebox.showerror("FFmpeg missing", msg)

    def _current_settings(self):
        fmt = self.fmt_var.get()
        if fmt:
            self.last_formats[self.selected_cat.get()] = fmt

        return {
            "geometry": self.root.geometry(),
            "selected_cat": self.selected_cat.get(),
            "formats": self.last_formats,
            "quality": self.quality_var.get(),
            "same_folder": self.same_folder.get(),
            "output_folder": (
                "" if self.same_folder.get()
                else self.output_folder.get().strip()
            ),
        }

    def _save_settings(self):
        save_settings(self._current_settings())

    def _on_close(self):
        self._save_settings()
        self.root.destroy()

    # ──────────────────────────────────────────────
    # CONVERSION
    # ──────────────────────────────────────────────
    def _start(self):
        if self.is_running:
            return

        cat    = self.selected_cat.get()
        if cat != "DOCUMENT" and not os.path.exists(FFMPEG_EXE):
            messagebox.showerror("FFmpeg missing",
                                 f"Cannot find FFmpeg:\n{FFMPEG_EXE}")
            return

        fmt_nm = self.fmt_var.get()
        if not fmt_nm:
            messagebox.showwarning("No Format", "Please select a conversion format.")
            return

        if not self.queued_files:
            messagebox.showwarning("No Files",
                                   "Please add at least one file to the queue.")
            return

        if self.same_folder.get():
            out_folder = None
        else:
            out_folder = self.output_folder.get().strip()
            if not out_folder or out_folder == "<same as source>":
                messagebox.showwarning("No Output",
                                       "Please select an output folder.")
                return

        active_files = [
            fp for fp in self.queued_files
            if self._category_for_file(fp) == cat
        ]
        skipped_inactive = len(self.queued_files) - len(active_files)
        if not active_files:
            messagebox.showwarning(
                "No Matching Files",
                f"The queue has no {cat.lower()} files for the active tab."
            )
            return

        fmt_info    = MODES[cat]["formats"][fmt_nm]
        qual_params = AUDIO_QUALITY.get(self.quality_var.get(),
                                        ["-acodec", "pcm_s24le"])
        files       = list(active_files)
        self._save_settings()

        self.is_running = True
        self.convert_btn.config(state="disabled", text="⏳  CONVERTING…")
        self.progress.config(maximum=len(files), value=0)
        self._set_status(f"Converting {len(files)} file(s)…")

        self._log("━" * 44, "hdr")
        self._log(f"  Format : {fmt_nm}", "hdr")
        self._log(f"  Files  : {len(files)}", "hdr")
        if skipped_inactive:
            self._log(f"  Skipped: {skipped_inactive} file(s) from other tabs", "warn")
        self._log("━" * 44, "hdr")

        def worker():
            success = errors = 0
            for i, fp in enumerate(files):
                fname = os.path.basename(fp)
                dest  = out_folder if out_folder else os.path.dirname(fp)
                self.root.after(0, self._log,
                                f"[{i+1}/{len(files)}]  {fname}", "info")
                try:
                    os.makedirs(dest, exist_ok=True)
                    _, out_name = convert_file(fp, dest, fmt_info, qual_params)
                    self.root.after(0, self._log, f"  ✓  {out_name}", "ok")
                    success += 1
                except Exception as e:
                    self.root.after(0, self._log, f"  ✗  {e}", "err")
                    errors += 1
                self.root.after(
                    0,
                    lambda done=i + 1: self.progress.config(value=done)
                )
                self.root.after(
                    0,
                    self._set_status,
                    f"Converted {i+1}/{len(files)} file(s)…"
                )
            self.root.after(0, self._finish, success, errors)

        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, success, errors):
        self.is_running = False
        self.convert_btn.config(state="normal", text="▶   CONVERT")
        self._log("━" * 44, "hdr")
        self._log(f"  Done — ✓ {success} succeeded   ✗ {errors} failed", "warn")
        self._set_status(f"Done — {success} OK, {errors} failed")

        if errors == 0:
            messagebox.showinfo("Complete",
                                f"All {success} file(s) converted successfully!")
        else:
            messagebox.showwarning("Finished with errors",
                                   f"{success} converted, {errors} failed.\n"
                                   f"See the log for details.")


# ==========================
# ENTRY POINT
# ==========================
if __name__ == "__main__":
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except ImportError:
        root = tk.Tk()

    app = MediaForge(root)
    root.mainloop()
