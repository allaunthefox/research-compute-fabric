#!/usr/bin/env python3
"""
servo_fetch_adapter.py — Servo-Fetch implementation for SwarmWebSurface

Integrates the high-performance, GPU-less Servo browser engine into the 
Sovereign Stack's web interaction surface.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import time

from infra.web_interaction_surface import WebInteractionSurface, WebTask, DutyType

class ServoFetchSurface(WebInteractionSurface):
    """
    Real implementation of WebInteractionSurface using servo-fetch.
    """
    
    def __init__(self, binary_path: Optional[str] = None):
        super().__init__()
        # Priority order: explicitly passed path -> env var -> standard tool path -> PATH
        self.binary_path = (
            binary_path or 
            os.getenv("SERVO_FETCH_PATH") or 
            str(Path(__file__).parent.parent / "tools" / "bin" / "servo-fetch")
        )
        
        # Verify binary exists or is in PATH
        if not Path(self.binary_path).exists() and subprocess.run(["which", "servo-fetch"], capture_output=True).returncode != 0:
            print(f"Warning: servo-fetch binary not found at {self.binary_path} or in PATH", file=os.sys.stderr)

    def _execute_servo(self, args: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
        """Run the servo-fetch binary."""
        cmd = [self.binary_path] + args
        
        # Add xvfb-run if requested or if we detect we're headless and it's available
        # On some systems, servo-fetch might need a dummy display
        if os.getenv("USE_XVFB") == "1" or (not os.getenv("DISPLAY") and subprocess.run(["which", "xvfb-run"], capture_output=True).returncode == 0):
            cmd = ["xvfb-run", "--auto-servernum"] + cmd
            
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"servo-fetch timed out after {timeout}s")
        except Exception as e:
            raise RuntimeError(f"Failed to execute servo-fetch: {e}")

    def _simulate_execution(self, task: WebTask) -> Dict[str, Any]:
        """
        Override the simulation with real execution.
        Note: The base class calls this from execute_task.
        """
        url = task.url
        options = task.options or {}
        
        # Map DutyType to servo-fetch CLI arguments
        if task.duty_type == DutyType.WEB_NAVIGATION or task.duty_type == DutyType.CONTENT_EXTRACTION:
            args = [url]
            if options.get("json"):
                args.append("--json")
            if options.get("selector"):
                args.extend(["--selector", options["selector"]])
            if options.get("timeout"):
                args.extend(["--timeout", str(options["timeout"])])
            if options.get("settle"):
                args.extend(["--settle", str(options["settle"])])
                
            proc = self._execute_servo(args)
            
            if proc.returncode != 0:
                return {"error": proc.stderr, "exit_code": proc.returncode}
                
            # If JSON mode, parse it
            if "--json" in args:
                try:
                    return json.loads(proc.stdout)
                except:
                    return {"content": proc.stdout}
            return {"content": proc.stdout}

        elif task.duty_type == DutyType.SCREENSHOT_CAPTURE:
            temp_path = options.get("path") or f"/tmp/screenshot_{task.task_id}.png"
            args = [url, "--screenshot", temp_path]
            if options.get("full_page"):
                args.append("--full-page")
                
            proc = self._execute_servo(args)
            if proc.returncode != 0:
                return {"error": proc.stderr, "exit_code": proc.returncode}
                
            return {
                "screenshot_path": temp_path,
                "url": url,
                "timestamp": time.time()
            }

        elif task.duty_type == DutyType.DISTRIBUTED_CRAWL:
            # For crawling, we use the 'crawl' subcommand
            args = ["crawl", url]
            if options.get("limit"):
                args.extend(["--limit", str(options["limit"])])
            if options.get("depth"):
                args.extend(["--max-depth", str(options["depth"])])
            if options.get("json"):
                args.append("--json")
                
            proc = self._execute_servo(args)
            if proc.returncode != 0:
                return {"error": proc.stderr, "exit_code": proc.returncode}
                
            # servo-fetch crawl returns NDJSON
            results = []
            for line in proc.stdout.splitlines():
                if line.strip():
                    try:
                        results.append(json.loads(line))
                    except:
                        results.append({"raw": line})
            
            return {
                "pages_crawled": len(results),
                "results": results
            }

        return {"error": f"DutyType {task.duty_type} not implemented in ServoFetchSurface"}

# ═══════════════════════════════════════════════════════════════════════════
# Simplified Swarm Interface
# ═══════════════════════════════════════════════════════════════════════════

class ServoSwarmInterface:
    def __init__(self, binary_path: Optional[str] = None):
        self.surface = ServoFetchSurface(binary_path)
    
    def fetch(self, url: str, **kwargs) -> Dict[str, Any]:
        # Ensure url is not in kwargs to avoid double passing
        kwargs.pop("url", None)
        task_info = self.surface.submit_task(DutyType.CONTENT_EXTRACTION, url, options=kwargs)
        return self.surface.execute_task(task_info["task_id"])

    def screenshot(self, url: str, path: str, **kwargs) -> Dict[str, Any]:
        kwargs.pop("url", None)
        kwargs["path"] = path
        task_info = self.surface.submit_task(DutyType.SCREENSHOT_CAPTURE, url, options=kwargs)
        return self.surface.execute_task(task_info["task_id"])

    def crawl(self, url: str, **kwargs) -> Dict[str, Any]:
        kwargs.pop("url", None)
        task_info = self.surface.submit_task(DutyType.DISTRIBUTED_CRAWL, url, options=kwargs)
        return self.surface.execute_task(task_info["task_id"])
