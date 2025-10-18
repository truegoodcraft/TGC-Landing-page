# Google Drive Read Plugin for TGC Core v2

This repository contains a Core v2 plugin that exposes read-only Google Drive
capabilities powered by BUS OAuth. The plugin follows the Core sandbox rules
and relies exclusively on Core-managed connection brokering.

## Repository layout

```
plugins/google_drive_read/
  __init__.py
  plugin.py
  capabilities.py
  services/
    __init__.py
    files.py
  settings.schema.json
core/
  contracts/
    plugin_v2.py (type stubs)
  conn_broker.py (type stubs)
  secrets.py (testing helper)
  capabilities.py (testing helper)
```

## BUS OAuth configuration

1. Configure Core with a BUS OAuth profile pointing at Google using the auth
   profile id `bus:google` (`<AUTH_PROFILE_ID>`).
2. Ensure the BUS deployment is reachable from Core (`<BUS_REPO_URL>` for
   reference).
3. Grant the profile the scopes required by this plugin:
   - `https://www.googleapis.com/auth/drive.readonly`
   - `https://www.googleapis.com/auth/drive.metadata.readonly`

Core and BUS handle the device-code or client credentials flow; the plugin only
requests brokered handles.

## Non-secret settings

Use Core to supply settings (non-secret) for the plugin. Example payload:

```json
{
  "auth_profile": "bus:google",
  "folder_allowlist": ["root", "abc123"],
  "mime_allowlist": ["application/pdf", "application/vnd.google-apps.document"],
  "max_page_size": 150
}
```

These values align with `plugins/google_drive_read/settings.schema.json`.

## Registering the plugin with Core

1. Build and publish the plugin package to `<NEW_PLUGIN_REPO_URL>` or install it
   directly inside the Core runtime environment.
2. Add the plugin to the Core plugin registry referencing `plugins.google_drive_read`.
3. Ensure the broker allow-list includes:
   - `www.googleapis.com`
   - `oauth2.googleapis.com`
   - `accounts.google.com`

## Capability readiness flow

1. `GET /plugins` — verify the plugin appears with `ready=false` until BUS/Core
   complete the authorization.
2. `POST /probe` with the plugin id; Core invokes `probe()` and surfaces
   `"state":"ready"` once the broker reports an authorized handle.
3. `GET /capabilities` — once ready, the manifest advertises `google.drive.read`
   with services `google.drive.files.list` and `google.drive.files.get`.

## Example Core requests (placeholders)

```bash
# Inspect plugin registration
curl -H "X-Session-Token: <token>" https://core.example.com/plugins

# Trigger probe
curl -X POST -H "X-Session-Token: <token>" \
     -d '{"plugin_id":"google_drive_read"}' \
     https://core.example.com/probe

# List capabilities once authorized
curl -H "X-Session-Token: <token>" https://core.example.com/capabilities

# Dry-run transform invoking list_files
curl -X POST -H "X-Session-Token: <token>" \
     -H "Content-Type: application/json" \
     -d '{
           "plugin_id": "google_drive_read",
           "service": "google.drive.files.list",
           "arguments": {
             "query": {"folder_id": "root", "page_size": 10}
           },
           "dry_run": true
         }' \
     https://core.example.com/execTransform
```

The dry run returns a read-only proposal describing the Drive query; no writes
are performed by the plugin.

## Running tests locally

```bash
pip install -r requirements-dev.txt  # if desired, optional for pytest
pytest
```

## Day-1 Acceptance Checklist

- [ ] Plugin package installed and registered within Core
- [ ] BUS auth profile `bus:google` configured and authorized
- [ ] Broker allow-list updated for Google domains
- [ ] Plugin probe reports ready within 2 seconds
- [ ] `/capabilities` shows `google.drive.read` services

