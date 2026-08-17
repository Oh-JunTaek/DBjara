"""
LCU (League Client Update) API Connector & Process Controller
Handles communication with the local League Client and enforces Solo Rank blocks.
"""

import os
import re
import ssl
import base64
import json
import subprocess
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Tuple
import psutil

# Disable SSL verification for self-signed certificates used by Riot Client
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


class LCUClient:
    def __init__(self):
        self.port: Optional[int] = None
        self.auth_token: Optional[str] = None
        self.auth_header: Optional[str] = None
        self._connected: bool = False

    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        """Attempt to find port and auth token from running LeagueClientUx.exe process."""
        port, token = self._find_credentials_from_process()
        if not port or not token:
            port, token = self._find_credentials_from_lockfile()

        if port and token:
            self.port = port
            self.auth_token = token
            auth_str = f"riot:{token}"
            encoded = base64.b64encode(auth_str.encode("ascii")).decode("ascii")
            self.auth_header = f"Basic {encoded}"
            self._connected = True
            return True

        self._connected = False
        return False

    def _find_credentials_from_process(self) -> Tuple[Optional[int], Optional[str]]:
        """Extract credentials from LeagueClientUx.exe command-line arguments."""
        try:
            for proc in psutil.process_iter(["name", "cmdline"]):
                if proc.info["name"] and proc.info["name"].lower() == "leagueclientux.exe":
                    cmdline = proc.info.get("cmdline") or []
                    cmd_str = " ".join(cmdline)

                    port_match = re.search(r"--app-port=([0-9]+)", cmd_str)
                    if not port_match:
                        port_match = re.search(r"--riotclient-app-port=([0-9]+)", cmd_str)

                    token_match = re.search(r"--remoting-auth-token=([\w-]+)", cmd_str)

                    if port_match and token_match:
                        return int(port_match.group(1)), token_match.group(1)
        except Exception as e:
            print(f"[LCU] Error inspecting processes: {e}")
        return None, None

    def _find_credentials_from_lockfile(self) -> Tuple[Optional[int], Optional[str]]:
        """Search standard lockfile locations."""
        potential_paths = [
            r"C:\Riot Games\League of Legends\lockfile",
            r"D:\Riot Games\League of Legends\lockfile",
            r"E:\Riot Games\League of Legends\lockfile",
        ]
        for path in potential_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        # Format: ProcessName:PID:Port:Password:Protocol
                        parts = content.split(":")
                        if len(parts) >= 5:
                            return int(parts[2]), parts[3]
                except Exception:
                    pass
        return None, None

    def request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, Optional[Dict[str, Any]]]:
        """Send an HTTP request to the local LCU API."""
        if not self._connected or not self.port or not self.auth_header:
            if not self.connect():
                return 0, None

        url = f"https://127.0.0.1:{self.port}{endpoint}"
        headers = {
            "Authorization": self.auth_header,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=2.0) as resp:
                status = resp.getcode()
                content = resp.read()
                if content:
                    try:
                        return status, json.loads(content.decode("utf-8"))
                    except Exception:
                        return status, {}
                return status, {}
        except urllib.error.HTTPError as e:
            # Client closed or endpoint returned error code
            if e.code == 404:
                return 404, None
            return e.code, None
        except Exception:
            # Connection lost (e.g. client closed)
            self._connected = False
            return 0, None

    def get_lobby(self) -> Optional[Dict[str, Any]]:
        """Get current lobby details."""
        status, data = self.request("GET", "/lol-lobby/v2/lobby")
        if status == 200 and isinstance(data, dict):
            return data
        return None

    def get_party_size(self) -> int:
        """Returns the number of members in current party lobby. Returns 0 if not in lobby."""
        lobby = self.get_lobby()
        if lobby and "members" in lobby and isinstance(lobby["members"], list):
            return len(lobby["members"])
        return 0

    def get_matchmaking_search_state(self) -> Optional[str]:
        """Returns current matchmaking search state (e.g. 'Searching', 'Found', 'Invalid')."""
        status, data = self.request("GET", "/lol-lobby/v2/lobby/matchmaking/search")
        if status == 200 and isinstance(data, dict):
            return data.get("searchState") or data.get("state")
        return None

    def cancel_matchmaking(self) -> bool:
        """Cancel current matchmaking search."""
        status, _ = self.request("DELETE", "/lol-lobby/v2/lobby/matchmaking/search")
        return status in (200, 204)

    def get_gameflow_phase(self) -> str:
        """
        Returns gameflow phase:
        'None', 'Lobby', 'Matchmaking', 'ReadyCheck', 'ChampSelect', 'InProgress', 'WaitingForStats', etc.
        """
        status, data = self.request("GET", "/lol-gameflow/v1/gameflow-phase")
        if status == 200 and isinstance(data, str):
            return data.strip('"')
        return "None"

    @staticmethod
    def is_league_running() -> bool:
        """Check if LeagueClient.exe or League of Legends.exe is currently running."""
        for proc in psutil.process_iter(["name"]):
            try:
                name = (proc.info["name"] or "").lower()
                if name in ("leagueclient.exe", "leagueclientux.exe", "league of legends.exe"):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False

    @staticmethod
    def kill_league_client() -> bool:
        """Force kill all League of Legends processes."""
        killed_any = False
        targets = ["league of legends.exe", "leagueclient.exe", "leagueclientux.exe", "leagueclientuxrender.exe"]
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info["name"] or "").lower()
                if name in targets:
                    proc.kill()
                    killed_any = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return killed_any
