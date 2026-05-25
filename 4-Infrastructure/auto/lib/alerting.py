#!/usr/bin/env python3
"""Alerting: email via local postfix, optional webhook, optional kuma push."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any


class Alerter:
    def __init__(self, config: dict[str, Any]) -> None:
        alert_cfg = config.get("alerting", {})
        email_cfg = alert_cfg.get("email", {})
        webhook_cfg = alert_cfg.get("webhook", {})
        dashboard_cfg = alert_cfg.get("dashboard", {})

        self.email_enabled = email_cfg.get("enabled", False)
        self.email_to = email_cfg.get("to", "")
        self.email_relay_ssh_target = email_cfg.get(
            "relay_ssh_target",
            os.environ.get("RS_ALERT_RELAY_SSH_TARGET", ""),
        )
        self.sendmail_path = email_cfg.get("sendmail_path", "/usr/sbin/sendmail")
        self.webhook_enabled = webhook_cfg.get("enabled", False)
        self.webhook_url = webhook_cfg.get("url", "")
        self.dashboard_enabled = dashboard_cfg.get("enabled", False)
        self.dashboard_endpoint = dashboard_cfg.get("endpoint", "")

        self.alerts: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def alert(self, msg: str) -> None:
        self.alerts.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.info.append(msg)

    def _is_actionable(self) -> bool:
        return bool(self.alerts or self.warnings)

    def send(self, tick: int = 0) -> dict[str, Any]:
        """
        Dispatch all queued messages. Returns dispatch status dict.
        Only sends real alerts/warnings; info-level is logged to receipt only.
        """
        result: dict[str, Any] = {"email": False, "webhook": False, "dashboard": False}

        if self.email_enabled and self._is_actionable():
            result["email"] = self._send_email(tick)

        if self.webhook_enabled and self.webhook_url:
            result["webhook"] = self._send_webhook(tick)

        if self.dashboard_enabled and self.dashboard_endpoint:
            result["dashboard"] = self._push_dashboard(tick)

        return result

    def _build_body(self, tick: int) -> str:
        lines = [
            f"Subject: infra-controller report — tick {tick}",
            f"Time: {datetime.now(timezone.utc).isoformat()}",
            f"",
        ]
        if self.alerts:
            lines.append(f"--- ALERTS ({len(self.alerts)}) ---")
            lines.extend(f"  CRIT: {a}" for a in self.alerts)
            lines.append("")
        if self.warnings:
            lines.append(f"--- WARNINGS ({len(self.warnings)}) ---")
            lines.extend(f"  WARN: {w}" for w in self.warnings)
            lines.append("")
        if self.info:
            lines.append(f"--- INFO ({len(self.info)}) ---")
            lines.extend(f"  {i}" for i in self.info)
        return "\n".join(lines)

    def _send_email(self, tick: int) -> bool:
        try:
            msg = MIMEText(self._build_body(tick))
            msg["Subject"] = f"infra-controller tick {tick}"
            msg["From"] = "infra-controller@researchstack.info"
            msg["To"] = self.email_to

            if self.email_relay_ssh_target:
                remote = (
                    f"ALERT_TO={shlex.quote(self.email_to)} "
                    "send-alert "
                    f"{shlex.quote(msg['Subject'])} "
                    f"{shlex.quote(self._build_body(tick))}"
                )
                proc = subprocess.run(
                    [
                        "ssh",
                        "-o", "StrictHostKeyChecking=no",
                        self.email_relay_ssh_target,
                        remote,
                    ],
                    timeout=30,
                    capture_output=True,
                )
                return proc.returncode == 0

            proc = subprocess.run(
                [self.sendmail_path, "-t", "-oi"],
                input=msg.as_string().encode(),
                timeout=15,
                capture_output=True,
            )
            return proc.returncode == 0
        except Exception as exc:
            print(f"  alerting: email failed: {exc}", file=sys.stderr)
            return False

    def _send_webhook(self, tick: int) -> bool:
        try:
            import subprocess
            payload = {
                "tick": tick,
                "alerts": self.alerts,
                "warnings": self.warnings,
                "info": self.info,
            }
            subprocess.run(
                [
                    "curl", "-s", "-X", "POST",
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps(payload),
                    self.webhook_url,
                ],
                timeout=10,
                capture_output=True,
            )
            return True
        except Exception as exc:
            print(f"  alerting: webhook failed: {exc}", file=sys.stderr)
            return False

    def _push_dashboard(self, tick: int) -> bool:
        try:
            status = "up"
            if self.alerts:
                status = "down"
            elif self.warnings:
                status = "down"

            msg = f"{status} — tick {tick}"
            if self.alerts:
                msg += " | " + "; ".join(self.alerts[:2])
            elif self.warnings:
                msg += " | " + "; ".join(self.warnings[:2])

            subprocess.run(
                [
                    "curl", "-s", "-X", "POST",
                    "-d", f"status={status}&msg={msg}",
                    self.dashboard_endpoint,
                ],
                timeout=10,
                capture_output=True,
            )
            return True
        except Exception as exc:
            print(f"  alerting: dashboard push failed: {exc}", file=sys.stderr)
            return False
