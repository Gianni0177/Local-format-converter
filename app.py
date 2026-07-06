from __future__ import annotations

import argparse
import csv
from collections import deque
from datetime import datetime
import io
import itertools
import json
import mimetypes
import pathlib
import os
import socket
import subprocess
import sys
import tempfile
import threading
import webbrowser
import zipfile
from dataclasses import dataclass
from typing import Any

from imageio_ffmpeg import get_ffmpeg_exe
from PIL import Image
import tomli_w
import xmltodict
import yaml
from flask import Flask, jsonify, render_template, request, send_file

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

app = Flask(__name__)

STRUCTURED_FORMATS = {"json", "csv", "yaml", "toml", "xml", "txt", "md"}
AUDIO_FORMATS = {"mp3", "wav", "flac", "aac", "ogg", "m4a"}
VIDEO_FORMATS = {"mp4", "mkv", "mov", "avi", "webm"}
IMAGE_FORMATS = {"png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"}
MEDIA_FORMATS = AUDIO_FORMATS | VIDEO_FORMATS
BINARY_FORMATS = MEDIA_FORMATS | IMAGE_FORMATS
ALLOWED_FORMATS = STRUCTURED_FORMATS | BINARY_FORMATS
TEXT_FORMATS = {"txt", "md"}
LOG_BUFFER = deque(maxlen=400)
LOG_SEQ = itertools.count(1)
LOG_LOCK = threading.Lock()


@dataclass
class ConversionResult:
    payload: bytes
    mime_type: str
    extension: str


class ConversionError(Exception):
    pass


def _normalize_rel_name(filename: str) -> str:
    sanitized = str(filename or "file").replace("\\", "/")
    pure = pathlib.PurePosixPath(sanitized)
    if pure.is_absolute():
        pure = pathlib.PurePosixPath(*pure.parts[1:])
    parts = [part for part in pure.parts if part not in {".", "..", ""}]
    if not parts:
        return "file"
    return "/".join(parts)


def add_app_log(level: str, message: str) -> None:
    entry = {
        "id": next(LOG_SEQ),
        "level": level,
        "message": message,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }
    with LOG_LOCK:
        LOG_BUFFER.append(entry)


def _read_logs_since(since_id: int) -> list[dict[str, str | int]]:
    with LOG_LOCK:
        return [entry for entry in LOG_BUFFER if int(entry["id"]) > since_id]


def pick_port(host: str, start_port: int, attempts: int = 30) -> int:
    for port in range(start_port, start_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if sock.connect_ex((host, port)) != 0:
                return port
    return start_port


def detect_format(filename: str) -> str:
    suffix = pathlib.Path(filename).suffix.lower().lstrip(".")
    if suffix == "yml":
        return "yaml"
    if suffix in ALLOWED_FORMATS:
        return suffix
    raise ConversionError(f"Formato non supportato: {suffix or 'sconosciuto'}")


def decode_text(raw: bytes) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ConversionError("Impossibile decodificare il file di input")


def parse_content(text: str, source_format: str) -> Any:
    try:
        if source_format == "json":
            return json.loads(text)
        if source_format == "yaml":
            return yaml.safe_load(text)
        if source_format == "toml":
            return tomllib.loads(text)
        if source_format == "csv":
            reader = csv.DictReader(io.StringIO(text))
            return list(reader)
        if source_format == "xml":
            return xmltodict.parse(text)
        if source_format in TEXT_FORMATS:
            return text
    except Exception as exc:
        raise ConversionError(f"Errore parsing input {source_format}: {exc}") from exc
    raise ConversionError(f"Formato sorgente non valido: {source_format}")


def _is_binary_conversion_allowed(source_format: str, target_format: str) -> bool:
    if source_format in IMAGE_FORMATS and target_format in IMAGE_FORMATS:
        return True
    if source_format in VIDEO_FORMATS and target_format in MEDIA_FORMATS:
        return True
    if source_format in AUDIO_FORMATS and target_format in AUDIO_FORMATS:
        return True
    return False


def _convert_image(raw: bytes, source_format: str, target_format: str) -> ConversionResult:
    if source_format not in IMAGE_FORMATS or target_format not in IMAGE_FORMATS:
        raise ConversionError("Conversione immagine non valida")

    with Image.open(io.BytesIO(raw)) as img:
        img.load()
        normalized_target = "JPEG" if target_format in {"jpg", "jpeg"} else target_format.upper()

        if normalized_target in {"JPEG", "ICO"} and img.mode in {"RGBA", "LA", "P"}:
            img = img.convert("RGB")

        output = io.BytesIO()
        save_kwargs: dict[str, Any] = {}
        if normalized_target == "JPEG":
            save_kwargs["quality"] = 92
            save_kwargs["optimize"] = True
        img.save(output, format=normalized_target, **save_kwargs)
        payload = output.getvalue()

    guessed_mime = mimetypes.guess_type(f"file.{target_format}")[0] or "application/octet-stream"
    return ConversionResult(payload=payload, mime_type=guessed_mime, extension=target_format)


def _convert_media(raw: bytes, source_format: str, target_format: str) -> ConversionResult:
    if not _is_binary_conversion_allowed(source_format, target_format):
        raise ConversionError(
            "Conversione media non supportata: consentite audio->audio, video->video e video->audio"
        )

    ffmpeg_exe = get_ffmpeg_exe()
    with tempfile.TemporaryDirectory(prefix="format-forge-") as tmp_dir:
        in_path = pathlib.Path(tmp_dir) / f"input.{source_format}"
        out_path = pathlib.Path(tmp_dir) / f"output.{target_format}"
        in_path.write_bytes(raw)

        cmd = [ffmpeg_exe, "-y", "-i", str(in_path)]
        if target_format in AUDIO_FORMATS:
            cmd.append("-vn")
        cmd.append(str(out_path))

        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if completed.returncode != 0 or not out_path.exists():
            details = completed.stderr.strip().splitlines()
            last_line = details[-1] if details else "errore sconosciuto"
            raise ConversionError(f"FFmpeg non e riuscito a convertire il file: {last_line}")

        payload = out_path.read_bytes()

    guessed_mime = mimetypes.guess_type(f"file.{target_format}")[0] or "application/octet-stream"
    return ConversionResult(payload=payload, mime_type=guessed_mime, extension=target_format)


def _to_csv_rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list) and all(isinstance(row, dict) for row in data):
        return data
    if isinstance(data, dict):
        list_values = [v for v in data.values() if isinstance(v, list) and all(isinstance(i, dict) for i in v)]
        if list_values:
            return list_values[0]
        if all(not isinstance(v, (dict, list)) for v in data.values()):
            return [data]
    raise ConversionError("Per esportare in CSV serve una lista di oggetti o un dizionario semplice")


def serialize_content(data: Any, target_format: str) -> ConversionResult:
    if target_format == "json":
        text = json.dumps(data, indent=2, ensure_ascii=False)
        return ConversionResult(text.encode("utf-8"), "application/json", "json")

    if target_format == "yaml":
        text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        return ConversionResult(text.encode("utf-8"), "application/x-yaml", "yaml")

    if target_format == "toml":
        toml_data: dict[str, Any]
        if isinstance(data, dict):
            toml_data = data
        else:
            toml_data = {"items": data}
        text = tomli_w.dumps(toml_data)
        return ConversionResult(text.encode("utf-8"), "application/toml", "toml")

    if target_format == "csv":
        rows = _to_csv_rows(data)
        output = io.StringIO()
        fieldnames: list[str] = sorted({key for row in rows for key in row.keys()})
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return ConversionResult(output.getvalue().encode("utf-8"), "text/csv", "csv")

    if target_format == "xml":
        if isinstance(data, dict) and len(data) == 1:
            text = xmltodict.unparse(data, pretty=True)
        else:
            text = xmltodict.unparse({"root": data}, pretty=True)
        return ConversionResult(text.encode("utf-8"), "application/xml", "xml")

    if target_format in TEXT_FORMATS:
        text = data if isinstance(data, str) else json.dumps(data, indent=2, ensure_ascii=False)
        mime = "text/markdown" if target_format == "md" else "text/plain"
        return ConversionResult(text.encode("utf-8"), mime, target_format)

    raise ConversionError(f"Formato target non valido: {target_format}")


def convert_uploaded_file(uploaded, source_format: str, target_format: str) -> tuple[ConversionResult, str]:
    filename = uploaded.filename or "file"
    resolved_source = source_format
    if not resolved_source or resolved_source == "auto":
        resolved_source = detect_format(filename)

    raw = uploaded.read()
    if resolved_source in BINARY_FORMATS or target_format in BINARY_FORMATS:
        if resolved_source not in BINARY_FORMATS or target_format not in BINARY_FORMATS:
            raise ConversionError("Non puoi mischiare conversioni binary con formati testuali/strutturati")
        if not _is_binary_conversion_allowed(resolved_source, target_format):
            raise ConversionError(
                "Conversione binary non supportata: immagini->immagini, audio->audio, video->video, video->audio"
            )
        if resolved_source in IMAGE_FORMATS and target_format in IMAGE_FORMATS:
            result = _convert_image(raw, resolved_source, target_format)
        else:
            result = _convert_media(raw, resolved_source, target_format)
    else:
        text = decode_text(raw)
        parsed = parse_content(text, resolved_source)
        result = serialize_content(parsed, target_format)

    output_name = f"{pathlib.Path(filename).stem}_converted.{result.extension}"
    return result, output_name


@app.route("/")
def index() -> str:
    desktop_mode = request.args.get("desktop") == "1"
    return render_template("index.html", formats=sorted(ALLOWED_FORMATS), desktop_mode=desktop_mode)


@app.route("/api/logs", methods=["GET"])
def api_logs():
    try:
        since_id = int(request.args.get("since", "0"))
    except ValueError:
        since_id = 0
    return jsonify({"logs": _read_logs_since(since_id)})


@app.route("/api/convert", methods=["POST"])
def convert_file():
    uploaded_files = request.files.getlist("file")
    uploaded_files = [item for item in uploaded_files if item and item.filename]
    target_format = (request.form.get("target_format") or "").lower().strip()

    if not uploaded_files:
        return jsonify({"error": "Carica un file prima di convertire"}), 400
    if target_format not in ALLOWED_FORMATS:
        return jsonify({"error": "Formato di destinazione non valido"}), 400

    source_format = (request.form.get("source_format") or "").lower().strip()

    try:
        if source_format and source_format != "auto":
            if source_format not in ALLOWED_FORMATS:
                raise ConversionError("Formato sorgente indicato non valido")

        detected_formats: list[str] = []
        if source_format != "auto":
            detected_formats = [source_format]
        else:
            detected_formats = [detect_format(item.filename) for item in uploaded_files]

        unique_source_formats = sorted(set(detected_formats))
        if len(unique_source_formats) > 1:
            raise ConversionError(
                "Nel caricamento multiplo o cartella i file devono avere lo stesso formato sorgente"
            )

        effective_source = unique_source_formats[0]
        if len(uploaded_files) > 1:
            add_app_log(
                "info",
                f"Conversione batch richiesta: {len(uploaded_files)} file ({effective_source} -> {target_format})",
            )
            zip_buffer = io.BytesIO()
            used_names: dict[str, int] = {}
            with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
                for uploaded in uploaded_files:
                    result, output_name = convert_uploaded_file(uploaded, source_format, target_format)
                    rel_name = _normalize_rel_name(uploaded.filename)
                    parent = pathlib.PurePosixPath(rel_name).parent
                    base_name = pathlib.Path(output_name).name

                    final_name = base_name
                    suffix = used_names.get(base_name, 0)
                    while final_name in used_names:
                        suffix += 1
                        stem = pathlib.Path(base_name).stem
                        ext = pathlib.Path(base_name).suffix
                        final_name = f"{stem}_{suffix}{ext}"
                    used_names[base_name] = max(used_names.get(base_name, 0), suffix)
                    used_names[final_name] = 1

                    arcname = str(parent / final_name) if str(parent) not in {"", "."} else final_name
                    archive.writestr(arcname, result.payload)

            zip_buffer.seek(0)
            add_app_log("ok", f"Conversione batch completata: {len(uploaded_files)} file")
            return send_file(
                zip_buffer,
                mimetype="application/zip",
                as_attachment=True,
                download_name="converted_batch.zip",
            )

        uploaded = uploaded_files[0]
        add_app_log("info", f"Conversione richiesta: {uploaded.filename} ({effective_source} -> {target_format})")
        result, output_name = convert_uploaded_file(uploaded, source_format, target_format)
        add_app_log("ok", f"Conversione completata: {output_name}")
        return send_file(
            io.BytesIO(result.payload),
            mimetype=result.mime_type,
            as_attachment=True,
            download_name=output_name,
        )
    except ConversionError as exc:
        add_app_log("error", f"Errore conversione: {exc}")
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        add_app_log("error", f"Errore interno: {exc}")
        return jsonify({"error": f"Errore interno: {exc}"}), 500


if __name__ == "__main__":
    is_frozen_exe = bool(getattr(sys, "frozen", False))
    host = os.getenv("HOST", "127.0.0.1")
    preferred_port = int(os.getenv("PORT", "5000"))

    auto_open_env = os.getenv("AUTO_OPEN_BROWSER")
    default_auto_open = is_frozen_exe
    if auto_open_env is not None:
        default_auto_open = auto_open_env.lower() in {"1", "true", "yes", "on"}

    parser = argparse.ArgumentParser(description="Format Forge")
    parser.add_argument("--host", default=host)
    parser.add_argument("--port", type=int, default=preferred_port)
    parser.add_argument("--debug", action="store_true", default=not is_frozen_exe)
    parser.add_argument("--no-debug", action="store_false", dest="debug")
    browser_group = parser.add_mutually_exclusive_group()
    browser_group.add_argument("--open-browser", action="store_true", dest="open_browser")
    browser_group.add_argument("--no-open-browser", action="store_false", dest="open_browser")
    parser.set_defaults(open_browser=default_auto_open)
    args = parser.parse_args()

    selected_port = pick_port(args.host, args.port)
    if selected_port != args.port:
        print(f"Porta {args.port} non disponibile. Avvio su {selected_port}.")

    add_app_log("info", f"Server avviato su http://{args.host}:{selected_port}")

    if args.open_browser:
        app_url = f"http://{args.host}:{selected_port}"
        # Delay breve per permettere al server Flask di essere in ascolto.
        threading.Timer(1.0, lambda: webbrowser.open(app_url)).start()

    app.run(
        host=args.host,
        port=selected_port,
        debug=args.debug,
        use_reloader=(args.debug and not is_frozen_exe),
    )
