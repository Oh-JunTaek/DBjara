"""
Riot Games API Cross-Validation Module for DBjara
Inspects recent match history (e.g. PC Cafe offline bypass detection) via Riot Match-V5 API.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Tuple, List, Optional, Dict, Any


class RiotAPIValidator:
    def __init__(self, api_key: str = "", region: str = "asia", platform: str = "kr"):
        self.api_key = api_key.strip()
        self.region = region.lower()
        self.platform = platform.lower()

    def get_puuid_by_riot_id(self, game_name: str, tag_line: str) -> Optional[str]:
        """Fetch PUUID by Riot ID (GameName#TagLine) via Riot Account-V1."""
        if not self.api_key:
            return None

        encoded_name = urllib.parse.quote(game_name.strip())
        encoded_tag = urllib.parse.quote(tag_line.strip())
        url = f"https://{self.region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encoded_name}/{encoded_tag}"

        req = urllib.request.Request(
            url,
            headers={"X-Riot-Token": self.api_key, "User-Agent": "DBjara-Validator"}
        )
        try:
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if resp.getcode() == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("puuid")
        except Exception as e:
            print(f"[RiotAPI] Error fetching PUUID: {e}")
        return None

    def get_recent_solo_matches(
        self, puuid: str, start_time_epoch: Optional[int] = None, count: int = 5
    ) -> List[str]:
        """
        Fetch recent Ranked Solo matches (Queue 420).
        Optionally filter matches created after start_time_epoch (in seconds).
        """
        if not self.api_key or not puuid:
            return []

        # queue=420 is Ranked Solo 5v5
        url = f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&count={count}"
        if start_time_epoch:
            url += f"&startTime={start_time_epoch}"

        req = urllib.request.Request(
            url,
            headers={"X-Riot-Token": self.api_key, "User-Agent": "DBjara-Validator"}
        )
        try:
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if resp.getcode() == 200:
                    matches = json.loads(resp.read().decode("utf-8"))
                    if isinstance(matches, list):
                        return matches
        except Exception as e:
            print(f"[RiotAPI] Error fetching matches: {e}")
        return []

    def check_for_illicit_solo_games(
        self, riot_id_full: str, start_time_epoch: int
    ) -> Tuple[bool, int, List[str]]:
        """
        Check if any solo rank matches were played since start_time_epoch.
        Returns (has_illicit_games, count_of_games, match_ids)
        """
        if not self.api_key or "#" not in riot_id_full:
            return False, 0, []

        parts = riot_id_full.split("#", 1)
        game_name, tag_line = parts[0], parts[1]

        puuid = self.get_puuid_by_riot_id(game_name, tag_line)
        if not puuid:
            return False, 0, []

        matches = self.get_recent_solo_matches(puuid, start_time_epoch=start_time_epoch)
        if matches:
            return True, len(matches), matches
        return False, 0, []
