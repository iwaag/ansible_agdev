# API

Minimal FastAPI webhook server for this Ansible repository.

## Run locally

From the repository root:

```bash
cd api
uv sync
WEBHOOK_TOKEN=change-me uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The server runs playbooks from the repository root and expects:

- `ansible-playbook` to be available in the container or host
- `ansible.cfg` in the repository root
- SSH key and Vault password file to already be mounted or present

## Endpoints

- `GET /healthz`
- `POST /webhook/configure/suspend/linux`
- `POST /webhook/suspend/linux`
- `POST /webhook/configure/suspend/macos`
- `POST /webhook/sleep/macos`
- `POST /webhook/configure/wol/linux`
- `POST /webhook/wake`
- `POST /webhook/wake/linux`
- `POST /webhook/wake/macos`

All POST endpoints require:

- header: `X-Webhook-Token: <token>`

Example body:

```json
{
  "limit": "agpc",
  "connection_path": "tailscale"
}
```

`connection_path` is optional and only accepts `local` or `tailscale`.
The request body itself is also optional, so sending `{}` or no JSON body is valid.
