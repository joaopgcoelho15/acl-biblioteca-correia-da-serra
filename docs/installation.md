# Installation and data

## Runtime

The application uses Python, Flask, pandas and openpyxl. Docker uses Python 3.11 and Gunicorn. Dependency versions are preserved as supplied in `requirements.txt`; this deposit does not claim a new dependency or security audit.

Supply `database.xlsx` in the repository root before starting:

```sh
docker compose up --build
```

Open `http://localhost:5057/`. The example binds only to `127.0.0.1:5057`, with an empty `URL_PREFIX`. A reverse-proxy installation can set that variable to its published path. Configure HTTPS, access controls and proxy settings separately before institutional deployment. The Python development entry point enables Flask debug mode; use Gunicorn for deployment.

## Spreadsheet

The application reads `Sheet1` from `database.xlsx`. The working dataset has these columns:

```text
id, path, page, Bibliographic Description, description, classification,
author, titulo, date, local, tomos, URL, lingua, carreira, notas, registo,
editor, local(atual), estado, editor_name, tradutor
```

Keep these names. `id` identifies the application record. The manuscript number parsed from an image filename is not necessarily the same identifier. `path` is relative to `website/`, normally `static/<image filename>`. `URL` can contain multiple links separated by line breaks.

To update the catalog, validate a replacement export, preserve IDs and image paths, then replace `database.xlsx` without changing its column names or sheet name. Request handlers read this file. Restarting the deployment after replacing data and assets provides a straightforward handoff.

## Additional inputs

- Manuscript images belong in `website/static/`, using the spreadsheet paths.
- The PDF download expects `server/catalogo.pdf`.
- Book covers and their mapping belong in `website/static/obras/`. Without `manifest.json`, cover-image associations are empty.
- `scripts/atualizar_imagens_obras.py` reads `Url de obras.xlsx` by default. Its `--excel` option selects another authorized source. Check source URLs and reuse permissions before downloading images.
- `scripts/importar_thumbnails.py` imports local thumbnails. Review its source-directory assumptions before using it on another machine.

These installation inputs are excluded from Git. The fixed-page illustrations included here do not constitute the complete digitized collection.
