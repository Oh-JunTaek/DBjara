"""
DBjara - 라이엇 공식 API 전적 교차 검증 모듈
Riot Match-V5 API를 통해 최근 솔로 랭크 플레이 내역(PC방 등 외부 플레이)을 감지합니다.
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
        """Riot ID(소환사명#태그)로 Riot Account-V1 API를 호출하여 PUUID를 조회합니다."""
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
            print(f"[RiotAPI] PUUID 조회 오류: {e}")
        return None

    def get_recent_solo_matches(
        self, puuid: str, start_time_epoch: Optional[int] = None, count: int = 5
    ) -> List[str]:
        """
        최근 솔로 랭크(Queue 420) 매치 ID 목록을 조회합니다.
        start_time_epoch(초 단위 타임스탬프) 이후의 게임만 필터링 가능합니다.
        """
        if not self.api_key or not puuid:
            return []

        # queue=420: 솔로 랭크 5v5
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
            print(f"[RiotAPI] 매치 목록 조회 오류: {e}")
        return []

    def check_for_illicit_solo_games(
        self, riot_id_full: str, start_time_epoch: int
    ) -> Tuple[bool, int, List[str]]:
        """
        특정 기준 시각 이후에 플레이된 솔로 랭크 게임이 있는지 검증합니다.
        반환값: (위반_게임_존재_여부, 판수, 매치_ID_목록)
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
