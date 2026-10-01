# Biblioteca Correia da Serra

Repository prepared for the public consultation application developed for the Biblioteca Correia da Serra at the Academia das Ciências de Lisboa.

This repository is private pending review. The source was deposited on 1 October 2026 from the local working copy, whose latest application changes are dated 4 August 2026. This is a source snapshot, not a verified copy of the current server deployment. Working spreadsheets, credentials and backups are excluded.

## Contents

- `server/app.py`: Flask application, search, filters, record views and Portuguese/English pages.
- `templates/`: Jinja templates.
- `website/`: styling and selected assets used by the fixed pages, without the complete manuscript image collection or book covers.
- `scripts/`: tools for importing and updating book-cover images.
- `Dockerfile`, `compose.yaml`, `requirements.txt`: runtime setup.
- [Installation and data](docs/installation.md): required spreadsheet, assets and update procedure.

The spreadsheet supplies the catalog data. A clone alone does not provide a working catalog until a validated `database.xlsx` is supplied. The manuscript PDF and full image collection must also be supplied separately for their views and download links.

## Related material

Analysis and dissertation supporting material are organized in [thesis-digital-information-management](https://github.com/joaopgcoelho15/thesis-digital-information-management), initially private.
