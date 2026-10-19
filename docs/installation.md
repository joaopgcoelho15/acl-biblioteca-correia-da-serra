# Installation and data

## Runtime

The application uses Python, Flask, pandas and openpyxl. Docker uses Python 3.11 and Gunicorn. Dependency versions are preserved as supplied in `requirements.txt`; this deposit does not claim a new dependency or security audit.

The repository includes `database.xlsx`, the manuscript PDF, book covers and
their image mapping. Start the application with:

```sh
docker compose up --build
```

Open `http://localhost:5057/acl-novo/`. The current `docker-compose.yml` publishes
port `5057` with `URL_PREFIX=/acl-novo`. Configure HTTPS, access controls and
proxy settings separately before institutional deployment. Bind to loopback
instead if the application should only be reachable from a local reverse proxy.
The Python development entry point enables Flask debug mode; use Gunicorn for deployment.

## Spreadsheet

The application reads `Sheet1` from `database.xlsx`. The working dataset has these columns:

```text
id, path, page, Bibliographic Description, description, classification,
author, titulo, date, local, tomos, URL, lingua, carreira, notas, registo,
Impressor, local(atual), estado, editor_name, tradutor
```

Keep these names. Column Q is now `Impressor`; legacy workbooks with `editor`
or `Editor` remain supported. The internal API field is still `editor`, and
editorial saves preserve the new spreadsheet header. Both applications read
the first sheet. Public pages do not need auxiliary sheets; the editorial app
can recreate `Chat` when adding a comment. Back up existing comments before
removing that sheet. `id` identifies the application record. The manuscript number parsed from an image filename is not necessarily the same identifier. `path` is relative to `website/`, normally `static/<image filename>`. `URL` can contain multiple links separated by line breaks.

To update the catalog, validate a replacement export, preserve IDs and image paths, then replace `database.xlsx` without changing its column names or sheet name. Request handlers read this file. Restarting the deployment after replacing data and assets provides a straightforward handoff.

## Additional inputs

- Manuscript images belong in `website/static/`, using the spreadsheet paths.
- The PDF download expects `server/catalogo.pdf`.
- Book covers and their mapping belong in `website/static/obras/`. Without `manifest.json`, cover-image associations are empty.
- `scripts/atualizar_imagens_obras.py` reads `Url de obras.xlsx` by default. Its `--excel` option selects another authorized source. Check source URLs and reuse permissions before downloading images.
- `scripts/importar_thumbnails.py` imports local thumbnails. Review its source-directory assumptions before using it on another machine.

These installation inputs are now included in Git. Local environments,
credentials, historical backups, duplicate thumbnail imports and download
diagnostics remain excluded. After changing data or images in a Docker
installation, rebuild with `docker compose up -d --build`.

`docs/deposit-sha256.txt` records checksums from the original source deposit;
it does not describe the updated files in this version.
