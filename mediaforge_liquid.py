import json
import os
import sys
import threading
from pathlib import Path

import audio_washer as washer


APP_NAME = "MediaForge"
HTML_FILE = "mediaforge_liquid.html"


def app_base_path():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def html_path():
    return app_base_path() / HTML_FILE


def category_extensions(category):
    return sorted(washer.INPUT_EXTS_BY_CATEGORY.get(category, []))


def file_filter(category):
    exts = category_extensions(category)
    if not exts:
        exts = washer.ALL_INPUT_EXTS
    wildcard = ";".join(f"*{ext}" for ext in exts)
    return f"{category.title()} files ({wildcard})"


class MediaForgeApi:
    def __init__(self):
        self._window = None
        self.files = []
        self.is_running = False
        self.category = "AUDIO"
        self.settings = washer.load_settings()

    def _bind(self, window):
        self._window = window

    def _emit(self, event, payload):
        if not self._window:
            return
        data = json.dumps(payload)
        self._window.evaluate_js(f"window.MediaForge && window.MediaForge.{event}({data});")

    def get_state(self):
        selected_cat = self.settings.get("selected_cat", "AUDIO")
        if selected_cat in washer.MODES:
            self.category = selected_cat

        return {
            "formats": {
                cat: list(info["formats"].keys())
                for cat, info in washer.MODES.items()
            },
            "audioQualities": list(washer.AUDIO_QUALITY.keys()),
            "ffmpegReady": os.path.exists(washer.FFMPEG_EXE),
            "ffprobeReady": os.path.exists(washer.FFPROBE_EXE),
            "ffmpegPath": washer.FFMPEG_EXE,
            "ffprobePath": washer.FFPROBE_EXE,
            "settings": {
                "category": self.category,
                "format": self.settings.get("formats", {}).get(self.category, ""),
                "quality": self.settings.get("quality", "24-bit WAV  (best)"),
                "sameFolder": self.settings.get("same_folder", False),
                "outputFolder": self.settings.get("output_folder", ""),
            },
        }

    def set_category(self, category):
        if category in washer.MODES:
            self.category = category
            self._save_settings({"selected_cat": category})
        return {"category": self.category}

    def choose_files(self, category):
        from webview import FileDialog

        self.set_category(category)
        result = self._window.create_file_dialog(
            FileDialog.OPEN,
            allow_multiple=True,
            file_types=(file_filter(category), "All files (*.*)"),
        )
        if result:
            return self.add_files(list(result), category)
        return {"added": 0, "files": self.files}

    def choose_queue_folder(self, category):
        from webview import FileDialog

        self.set_category(category)
        result = self._window.create_file_dialog(FileDialog.FOLDER)
        if result:
            return self.add_files(list(result), category)
        return {"added": 0, "files": self.files}

    def choose_output_folder(self):
        from webview import FileDialog

        result = self._window.create_file_dialog(FileDialog.FOLDER)
        if result:
            return result[0]
        return ""

    def _expand_paths(self, paths):
        files = []
        for raw_path in paths:
            path = os.path.abspath(str(raw_path))
            if os.path.isdir(path):
                for root, _, names in os.walk(path):
                    for name in names:
                        files.append(os.path.join(root, name))
            elif os.path.isfile(path):
                files.append(path)
        return files

    def _category_for_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        for cat, exts in washer.INPUT_EXTS_BY_CATEGORY.items():
            if ext in exts:
                return cat
        return None

    def add_files(self, paths, category=None):
        if category in washer.MODES:
            self.set_category(category)
        category = self.category

        added = 0
        skipped = 0
        duplicates = 0
        wrong_category = 0
        files = self._expand_paths(paths)
        detected = [(path, self._category_for_file(path)) for path in files]
        supported = [(path, cat) for path, cat in detected if cat]

        if supported and not any(cat == category for _, cat in supported):
            category = supported[0][1]
            self.set_category(category)
            self._emit("onCategory", {"category": category})

        accepted_exts = set(category_extensions(category))

        for path, detected_category in supported:
            if detected_category != category:
                wrong_category += 1
                continue
            ext = os.path.splitext(path)[1].lower()
            if ext not in accepted_exts:
                skipped += 1
                continue
            if path in self.files:
                duplicates += 1
                continue
            self.files.append(path)
            added += 1

        unsupported = len(detected) - len(supported)
        skipped += unsupported

        payload = {
            "files": self.files,
            "added": added,
            "skipped": skipped,
            "duplicates": duplicates,
            "wrongCategory": wrong_category,
            "category": category,
        }
        self._emit("onQueue", payload)
        return payload

    def clear_queue(self):
        self.files = []
        self._emit("onQueue", {"files": self.files, "added": 0, "skipped": 0})
        return {"files": self.files}

    def convert(self, options):
        if self.is_running:
            return {"ok": False, "message": "Conversion is already running."}

        category = options.get("category", "AUDIO")
        self.set_category(category)

        if category != "DOCUMENT" and not os.path.exists(washer.FFMPEG_EXE):
            return {"ok": False, "message": f"FFmpeg not found: {washer.FFMPEG_EXE}"}

        if not self.files:
            return {"ok": False, "message": "Add at least one file first."}

        fmt_name = options.get("format")
        output_folder = options.get("outputFolder", "").strip()
        same_folder = bool(options.get("sameFolder"))
        quality_name = options.get("quality")

        if category not in washer.MODES:
            return {"ok": False, "message": "Unknown media category."}
        if fmt_name not in washer.MODES[category]["formats"]:
            return {"ok": False, "message": "Choose a valid output format."}
        if not same_folder and not output_folder:
            return {"ok": False, "message": "Choose an output folder or enable same-folder output."}

        active_exts = set(category_extensions(category))
        files = [
            path for path in self.files
            if os.path.splitext(path)[1].lower() in active_exts
        ]
        if not files:
            return {"ok": False, "message": f"No {category.lower()} files in the queue."}

        self._save_settings({
            "selected_cat": category,
            "formats": {
                **self.settings.get("formats", {}),
                category: fmt_name,
            },
            "quality": quality_name,
            "same_folder": same_folder,
            "output_folder": "" if same_folder else output_folder,
        })

        fmt_info = washer.MODES[category]["formats"][fmt_name]
        quality_params = washer.AUDIO_QUALITY.get(
            quality_name,
            ["-acodec", "pcm_s24le"],
        )

        self.is_running = True
        worker = threading.Thread(
            target=self._convert_worker,
            args=(files, fmt_info, quality_params, output_folder, same_folder),
            daemon=True,
        )
        worker.start()
        return {"ok": True, "message": "Conversion started.", "total": len(files)}

    def _convert_worker(self, files, fmt_info, quality_params, output_folder, same_folder):
        success = 0
        errors = 0
        total = len(files)
        self._emit("onStart", {"total": total})

        for index, path in enumerate(files, start=1):
            name = os.path.basename(path)
            self._emit("onLog", {"type": "info", "message": f"[{index}/{total}] {name}"})
            try:
                dest = os.path.dirname(path) if same_folder else output_folder
                os.makedirs(dest, exist_ok=True)
                _, out_name = washer.convert_file(path, dest, fmt_info, quality_params)
                success += 1
                self._emit("onLog", {"type": "ok", "message": f"✓ {out_name}"})
            except Exception as exc:
                errors += 1
                self._emit("onLog", {"type": "err", "message": f"✗ {exc}"})

            self._emit(
                "onProgress",
                {
                    "done": index,
                    "total": total,
                    "percent": round(index * 100 / total),
                    "success": success,
                    "errors": errors,
                },
            )

        self.is_running = False
        self._emit("onFinish", {"success": success, "errors": errors, "total": total})

    def handle_drop(self, event):
        files = event.get("dataTransfer", {}).get("files", [])
        paths = [
            item.get("pywebviewFullPath")
            for item in files
            if item.get("pywebviewFullPath")
        ]
        if not paths:
            self._emit(
                "onLog",
                {
                    "type": "warn",
                    "message": "Drop received, but WebView did not provide file paths. Use Browse Files.",
                },
            )
            return
        self.add_files(paths, self.category)

    def _save_settings(self, patch):
        self.settings.update(patch)
        washer.save_settings(self.settings)


def main():
    try:
        import webview
    except ImportError:
        print("pywebview is required. Install it with: pip install pywebview")
        raise

    api = MediaForgeApi()
    window = webview.create_window(
        APP_NAME,
        html_path().as_uri(),
        js_api=api,
        width=1280,
        height=820,
        min_size=(980, 640),
    )
    api._bind(window)

    def on_loaded():
        from webview.dom import DOMEventHandler

        drop_zone = window.dom.get_element("#dropZone")
        if drop_zone:
            drop_zone.on(
                "drop",
                DOMEventHandler(
                    api.handle_drop,
                    prevent_default=True,
                    stop_propagation=True,
                ),
            )
        window.evaluate_js(
            "window.initBridge && window.initBridge();"
        )

    window.events.loaded += on_loaded
    webview.start(debug=False)


if __name__ == "__main__":
    main()
