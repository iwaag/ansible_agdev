from __future__ import annotations

import asyncio
import os
import re
import subprocess
from pathlib import Path
from typing import Final

from fastapi import Body, Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
TOKEN_ENV_NAME: Final[str] = "WEBHOOK_TOKEN"
SAFE_VALUE_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9_.:-]+$")

PLAYBOOKS: Final[dict[str, str]] = {
    "configure_suspend_linux": "playbooks/configure_suspend_sudo.yml",
    "suspend_linux": "playbooks/suspend_hosts.yml",
    "configure_suspend_macos": "playbooks/configure_suspend_mac.yml",
    "sleep_macos": "playbooks/sleep_macos_hosts.yml",
    "enable_wol_linux": "playbooks/enable_wake_on_lan.yml",
    "wake": "playbooks/wake_hosts.yml",
}

RUN_LOCK = asyncio.Lock()
app = FastAPI(title="Ansible Webhooks", version="0.1.0")


class PlaybookRequest(BaseModel):
    limit: str | None = Field(default=None, description="Inventory host or group selector")
    connection_path: str | None = Field(default=None, description="local or tailscale")


def _validate_value(name: str, value: str) -> str:
    if not SAFE_VALUE_RE.fullmatch(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {name}: {value!r}",
        )
    return value


def require_token(x_webhook_token: str | None = Header(default=None)) -> None:
    expected = os.getenv(TOKEN_ENV_NAME)
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{TOKEN_ENV_NAME} is not configured",
        )
    if x_webhook_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook token",
        )


def _build_command(playbook_key: str, payload: PlaybookRequest) -> list[str]:
    command = ["ansible-playbook", PLAYBOOKS[playbook_key]]

    if payload.limit:
        command.extend(["--limit", _validate_value("limit", payload.limit)])

    if payload.connection_path:
        connection_path = _validate_value("connection_path", payload.connection_path)
        if connection_path not in {"local", "tailscale"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="connection_path must be 'local' or 'tailscale'",
            )
        command.extend(["-e", f"connection_path={connection_path}"])

    return command


async def _run_playbook(playbook_key: str, payload: PlaybookRequest) -> dict[str, object]:
    command = _build_command(playbook_key, payload)

    async with RUN_LOCK:
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

    return {
        "ok": process.returncode == 0,
        "playbook": PLAYBOOKS[playbook_key],
        "command": command,
        "returncode": process.returncode,
        "stdout": stdout.decode(),
        "stderr": stderr.decode(),
    }


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


def _payload_or_default(payload: PlaybookRequest | None) -> PlaybookRequest:
    return payload if payload is not None else PlaybookRequest()


@app.post("/webhook/configure/suspend/linux", dependencies=[Depends(require_token)])
async def configure_suspend_linux(
    payload: PlaybookRequest | None = Body(default=None),
) -> dict[str, object]:
    return await _run_playbook("configure_suspend_linux", _payload_or_default(payload))


@app.post("/webhook/suspend/linux", dependencies=[Depends(require_token)])
async def suspend_linux(payload: PlaybookRequest | None = Body(default=None)) -> dict[str, object]:
    return await _run_playbook("suspend_linux", _payload_or_default(payload))


@app.post("/webhook/configure/suspend/macos", dependencies=[Depends(require_token)])
async def configure_suspend_macos(
    payload: PlaybookRequest | None = Body(default=None),
) -> dict[str, object]:
    return await _run_playbook("configure_suspend_macos", _payload_or_default(payload))


@app.post("/webhook/sleep/macos", dependencies=[Depends(require_token)])
async def sleep_macos(payload: PlaybookRequest | None = Body(default=None)) -> dict[str, object]:
    return await _run_playbook("sleep_macos", _payload_or_default(payload))


@app.post("/webhook/configure/wol/linux", dependencies=[Depends(require_token)])
async def enable_wol_linux(
    payload: PlaybookRequest | None = Body(default=None),
) -> dict[str, object]:
    return await _run_playbook("enable_wol_linux", _payload_or_default(payload))


@app.post("/webhook/wake", dependencies=[Depends(require_token)])
async def wake(payload: PlaybookRequest | None = Body(default=None)) -> dict[str, object]:
    return await _run_playbook("wake", _payload_or_default(payload))
