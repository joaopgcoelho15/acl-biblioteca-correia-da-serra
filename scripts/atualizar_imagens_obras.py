#!/usr/bin/env python3
"""Sincroniza imagens de obras a partir do ficheiro Excel do projeto."""

import argparse
import json
import os
import re
import tempfile
import time
import xml.etree.ElementTree as ET
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EXCEL = PROJECT_DIR / "Url de obras.xlsx"
DEFAULT_OUTPUT = PROJECT_DIR / "website" / "static" / "obras"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "relatorio.json"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Descarrega e atualiza as imagens indicadas na coluna C do Excel."
    )
    parser.add_argument("--excel", type=Path, default=DEFAULT_EXCEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--force", action="store_true", help="Volta a descarregar todas as imagens.")
    parser.add_argument("--limit", type=int, help="Limita os downloads; útil para testes.")
    return parser.parse_args()


def normalize_record_id(value):
    if value is None:
        return None
    if isinstance(value, (int, float)) and float(value).is_integer():
        return str(int(value))
    text = str(value).strip()
    if re.fullmatch(r"\d+(?:\.0+)?", text):
        return str(int(float(text)))
    return None


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def xml_name(namespace, name):
    return f"{{{namespace}}}{name}"


def shared_strings(archive):
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return [
        "".join(node.text or "" for node in item.iter(xml_name(MAIN_NS, "t")))
        for item in root.findall(xml_name(MAIN_NS, "si"))
    ]


def first_sheet_path(archive):
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    sheet = workbook.find(f".//{xml_name(MAIN_NS, 'sheet')}")
    relationship_id = sheet.attrib[xml_name(DOC_REL_NS, "id")]
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    for relationship in relationships.findall(xml_name(PKG_REL_NS, "Relationship")):
        if relationship.attrib.get("Id") == relationship_id:
            target = relationship.attrib["Target"].lstrip("/")
            return target if target.startswith("xl/") else f"xl/{target}"
    raise ValueError("Não foi possível localizar a primeira folha do Excel.")


def sheet_hyperlinks(archive, sheet_path, sheet_root):
    relationships_path = str(
        Path(sheet_path).parent / "_rels" / f"{Path(sheet_path).name}.rels"
    )
    try:
        relationships = ET.fromstring(archive.read(relationships_path))
        targets = {
            node.attrib.get("Id"): node.attrib.get("Target", "")
            for node in relationships.findall(xml_name(PKG_REL_NS, "Relationship"))
        }
    except KeyError:
        targets = {}

    return {
        node.attrib.get("ref"): targets.get(node.attrib.get(xml_name(DOC_REL_NS, "id")), "")
        for node in sheet_root.findall(f".//{xml_name(MAIN_NS, 'hyperlink')}")
    }


def cell_value(cell, strings):
    value_node = cell.find(xml_name(MAIN_NS, "v"))
    if value_node is None:
        inline = cell.find(xml_name(MAIN_NS, "is"))
        if inline is None:
            return ""
        return "".join(node.text or "" for node in inline.iter(xml_name(MAIN_NS, "t")))

    value = value_node.text or ""
    if cell.attrib.get("t") == "s":
        try:
            return strings[int(value)]
        except (ValueError, IndexError):
            return ""
    return value


def read_sources(excel_path):
    sources = {}
    ignored = 0
    invalid_ids = 0
    duplicates = []

    with zipfile.ZipFile(excel_path) as archive:
        strings = shared_strings(archive)
        sheet_path = first_sheet_path(archive)
        sheet = ET.fromstring(archive.read(sheet_path))
        hyperlinks = sheet_hyperlinks(archive, sheet_path, sheet)

        for row in sheet.findall(f".//{xml_name(MAIN_NS, 'row')}"):
            cells = {cell.attrib.get("r", "")[:1]: cell for cell in row}
            record_id = normalize_record_id(
                cell_value(cells["A"], strings) if "A" in cells else None
            )
            url = ""
            if "C" in cells:
                reference = cells["C"].attrib.get("r", "")
                url = hyperlinks.get(reference, "") or str(cell_value(cells["C"], strings)).strip()
            url = url if url.lower().startswith(("http://", "https://")) else None

            if not record_id:
                invalid_ids += 1
                continue
            if not url:
                ignored += 1
                continue
            if record_id in sources:
                duplicates.append(record_id)
            sources[record_id] = url

    return sources, ignored, invalid_ids, duplicates


def load_manifest(path):
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle).get("images", {})
    except (OSError, json.JSONDecodeError):
        return {}


def extension_for(data, content_type, url):
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if data.startswith(b"BM"):
        return "bmp"
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return "tif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data.startswith(b"\x00\x00\x00\x0cjP  \r\n\x87\n"):
        return "jp2"
    if data.lstrip().startswith(b"<svg"):
        return "svg"

    mime = content_type.split(";", 1)[0].strip().lower()
    mime_extensions = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
        "image/tiff": "tif",
        "image/bmp": "bmp",
        "image/svg+xml": "svg",
        "image/jp2": "jp2",
    }
    if mime in mime_extensions:
        return mime_extensions[mime]

    match = re.search(r"\.(jpe?g|png|gif|webp|tiff?|bmp|svg|jp2)(?:[?#]|$)", url, re.I)
    if match:
        return {"jpeg": "jpg", "tiff": "tif"}.get(match.group(1).lower(), match.group(1).lower())
    raise ValueError(f"a resposta não parece ser uma imagem ({content_type or 'sem Content-Type'})")


def download_one(record_id, url, output_dir, timeout, retries):
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    last_error = None

    for attempt in range(max(retries, 0) + 1):
        temp_path = None
        try:
            with urlopen(request, timeout=timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                chunks = []
                total = 0
                while True:
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > 40 * 1024 * 1024:
                        raise ValueError("imagem superior ao limite de 40 MB")
                    chunks.append(chunk)

            data = b"".join(chunks)
            if not data:
                raise ValueError("resposta vazia")
            extension = extension_for(data[:512], content_type, url)
            destination = output_dir / f"{record_id}.{extension}"
            with tempfile.NamedTemporaryFile(dir=output_dir, delete=False) as handle:
                handle.write(data)
                temp_path = Path(handle.name)
            os.replace(temp_path, destination)
            return {
                "record_id": record_id,
                "url": url,
                "file": f"static/obras/{destination.name}",
                "bytes": len(data),
            }
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as error:
            last_error = error
            if temp_path and temp_path.exists():
                temp_path.unlink()
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))

    raise RuntimeError(str(last_error))


def write_json(path, payload):
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temp_path, path)


def manifest_payload(images):
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "images": dict(sorted(images.items(), key=lambda item: int(item[0]))),
    }


def recover_downloaded_files(output_dir, sources, images):
    recovered = []
    pattern = re.compile(r"^(\d+)\.(?:jpg|png|gif|bmp|tif|webp|jp2|svg)$", re.I)
    for path in output_dir.iterdir():
        match = pattern.fullmatch(path.name)
        if not match:
            continue
        record_id = str(int(match.group(1)))
        if record_id in sources and record_id not in images:
            images[record_id] = {
                "file": f"static/obras/{path.name}",
                "source_url": sources[record_id],
                "bytes": path.stat().st_size,
            }
            recovered.append(record_id)
    return recovered


def main():
    args = parse_args()
    excel_path = args.excel.resolve()
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / MANIFEST_NAME

    sources, ignored, invalid_ids, duplicates = read_sources(excel_path)
    previous = load_manifest(manifest_path)
    current = dict(previous)
    recovered = recover_downloaded_files(output_dir, sources, current)

    removed = []
    for record_id in sorted(set(current) - set(sources), key=int):
        if current[record_id].get("source_type") == "local-thumbnail":
            continue
        old_file = PROJECT_DIR / "website" / current[record_id].get("file", "")
        if old_file.is_file():
            old_file.unlink()
        current.pop(record_id, None)
        removed.append(record_id)

    pending = []
    skipped = []
    for record_id, url in sources.items():
        old = current.get(record_id, {})
        old_file = PROJECT_DIR / "website" / old.get("file", "")
        if not args.force and old.get("source_url") == url and old_file.is_file():
            skipped.append(record_id)
        else:
            pending.append((record_id, url))

    if args.limit is not None:
        pending = pending[: max(args.limit, 0)]

    print(
        f"Excel: {len(sources)} URLs válidos; {ignored} linhas ignoradas; "
        f"{len(pending)} imagens para descarregar; {len(recovered)} recuperadas."
        , flush=True
    )

    downloaded = []
    failures = []
    with ThreadPoolExecutor(max_workers=max(args.workers, 1)) as executor:
        futures = {
            executor.submit(
                download_one, record_id, url, output_dir, args.timeout, args.retries
            ): (record_id, url)
            for record_id, url in pending
        }
        for position, future in enumerate(as_completed(futures), 1):
            record_id, url = futures[future]
            try:
                result = future.result()
                old = current.get(record_id, {})
                old_file = PROJECT_DIR / "website" / old.get("file", "")
                new_file = PROJECT_DIR / "website" / result["file"]
                if old_file.is_file() and old_file != new_file:
                    old_file.unlink()
                current[record_id] = {
                    "file": result["file"],
                    "source_url": result["url"],
                    "bytes": result["bytes"],
                }
                downloaded.append(record_id)
            except Exception as error:
                failures.append({"record_id": record_id, "url": url, "error": str(error)})

            if position % 25 == 0 or position == len(futures):
                write_json(manifest_path, manifest_payload(current))
                print(
                    f"Processadas {position}/{len(futures)}: "
                    f"{len(downloaded)} descarregadas, {len(failures)} falharam.",
                    flush=True,
                )

    timestamp = datetime.now(timezone.utc).isoformat()
    write_json(manifest_path, manifest_payload(current))
    missing = [
        {"record_id": record_id, "url": sources[record_id]}
        for record_id in sorted(set(sources) - set(current), key=int)
    ]
    write_json(
        output_dir / REPORT_NAME,
        {
            "generated_at": timestamp,
            "excel": str(excel_path),
            "valid_urls": len(sources),
            "available_images": len(current),
            "downloaded": downloaded,
            "recovered": recovered,
            "unchanged": skipped,
            "removed": removed,
            "ignored_rows": ignored,
            "invalid_record_ids": invalid_ids,
            "duplicate_record_ids": duplicates,
            "failures": failures,
            "missing": missing,
        },
    )

    print(
        f"Concluído: {len(downloaded)} descarregadas, {len(skipped)} sem alterações, "
        f"{len(removed)} removidas, {len(failures)} falharam e {len(missing)} continuam em falta.",
        flush=True,
    )
    if failures:
        print(f"Consulta os detalhes em {output_dir / REPORT_NAME}")


if __name__ == "__main__":
    main()
