#!/usr/bin/env python3
"""Importa thumbnails locais e regista-as como imagens de obras."""

import argparse
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_DIR / "Thumbnails"
DEFAULT_OUTPUT = PROJECT_DIR / "website" / "static" / "obras"
FILENAME_PATTERN = re.compile(r"^BDJ(?:CS|SC)_(\d+)\.(jpe?g|png)$", re.IGNORECASE)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Copia imagens de Thumbnails para website/static/obras."
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def load_manifest(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle).get("images", {})
    except (OSError, json.JSONDecodeError):
        return {}


def write_manifest(path, images):
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "images": dict(sorted(images.items(), key=lambda item: int(item[0]))),
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def detected_extension(path):
    header = path.read_bytes()[:16]
    if header.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    raise ValueError("o ficheiro não é uma imagem JPEG ou PNG válida")


def main():
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    images = load_manifest(manifest_path)
    imported = []
    ignored = []

    for path in sorted(source.iterdir()):
        if not path.is_file():
            continue
        match = FILENAME_PATTERN.fullmatch(path.name)
        if not match:
            ignored.append(path.name)
            continue

        record_id = str(int(match.group(1)))
        extension = detected_extension(path)
        destination = output / f"{record_id}.{extension}"
        previous = images.get(record_id, {})
        previous_file = PROJECT_DIR / "website" / previous.get("file", "")

        shutil.copy2(path, destination)
        if previous_file.is_file() and previous_file != destination:
            previous_file.unlink()

        images[record_id] = {
            "file": f"static/obras/{destination.name}",
            "source_file": f"Thumbnails/{path.name}",
            "source_type": "local-thumbnail",
            "bytes": destination.stat().st_size,
        }
        imported.append(record_id)

    write_manifest(manifest_path, images)
    print(f"Importadas {len(imported)} thumbnails; {len(ignored)} ficheiros ignorados.")
    if ignored:
        print("Ignorados: " + ", ".join(ignored))


if __name__ == "__main__":
    main()
