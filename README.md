# mentviro Instagram Automation

Täglich automatischer Post + Story um **18:00 Uhr** via GitHub Actions.

## Secrets setzen (einmalig)
`GitHub Repo → Settings → Secrets → Actions → New repository secret`

| Secret | Wert |
|--------|------|
| `COMPOSIO_API_KEY` | composio.dev → Profil → API Keys |
| `MENTVIRO_LOGO_URL` | Öffentliche URL deines Logo-PNGs (optional) |

## Neuen Post hinzufügen
Eintrag in `automation/content_plan.json` mit `"status": "pending"` hinzufügen.

## Manuell auslösen
GitHub → Actions → *mentviro Daily Instagram Post* → Run workflow
