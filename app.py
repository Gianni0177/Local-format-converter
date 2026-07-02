from __future__ import annotations

import csv
import io
import json
import mimetypes
import pathlib
import os
import socket
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Any

from imageio_ffmpeg import get_ffmpeg_exe
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
MEDIA_FORMATS = AUDIO_FORMATS | VIDEO_FORMATS
ALLOWED_FORMATS = STRUCTURED_FORMATS | MEDIA_FORMATS
TEXT_FORMATS = {"txt", "md"}


@dataclass
class ConversionResult:
    payload: bytes
    mime_type: str
    extension: str


class ConversionError(Exception):
    pass


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


def _is_media_conversion_allowed(source_format: str, target_format: str) -> bool:
    if source_format in VIDEO_FORMATS and target_format in MEDIA_FORMATS:
        return True
    if source_format in AUDIO_FORMATS and target_format in AUDIO_FORMATS:
        return True
    return False


def _convert_media(raw: bytes, source_format: str, target_format: str) -> ConversionResult:
    if not _is_media_conversion_allowed(source_format, target_format):
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


@app.route("/")
def index() -> str:
    return render_template("index.html", formats=sorted(ALLOWED_FORMATS))


@app.route("/api/convert", methods=["POST"])
def convert_file():
    uploaded = request.files.get("file")
    target_format = (request.form.get("target_format") or "").lower().strip()

    if not uploaded or not uploaded.filename:
        return jsonify({"error": "Carica un file prima di convertire"}), 400
    if target_format not in ALLOWED_FORMATS:
        return jsonify({"error": "Formato di destinazione non valido"}), 400

    source_format = (request.form.get("source_format") or "").lower().strip()

    try:
        if source_format and source_format != "auto":
            if source_format not in ALLOWED_FORMATS:
                raise ConversionError("Formato sorgente indicato non valido")
        else:
            source_format = detect_format(uploaded.filename)

        raw = uploaded.read()
        if source_format in MEDIA_FORMATS or target_format in MEDIA_FORMATS:
            if source_format not in MEDIA_FORMATS or target_format not in MEDIA_FORMATS:
                raise ConversionError("Non puoi mischiare conversioni media con formati testuali/strutturati")
            result = _convert_media(raw, source_format, target_format)
        else:
            text = decode_text(raw)
            parsed = parse_content(text, source_format)
            result = serialize_content(parsed, target_format)

        output_name = f"{pathlib.Path(uploaded.filename).stem}_converted.{result.extension}"
        return send_file(
            io.BytesIO(result.payload),
            mimetype=result.mime_type,
            as_attachment=True,
            download_name=output_name,
        )
    except ConversionError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Errore interno: {exc}"}), 500


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    preferred_port = int(os.getenv("PORT", "5000"))

    def pick_port(start_port: int) -> int:
        for port in range(start_port, start_port + 30):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                if sock.connect_ex((host, port)) != 0:
                    return port
        return start_port

    selected_port = pick_port(preferred_port)
    if selected_port != preferred_port:
        print(f"Porta {preferred_port} non disponibile. Avvio su {selected_port}.")

    app.run(host=host, port=selected_port, debug=True)
