from __future__ import annotations

import re
from typing import Any

from app.core.config import RONE_DEV_ACCESS_KEY
from app.core.http import MLBBHeaderBuilder, request_json
from app.core.security import BasePathProvider
from app.utils.client_ip import get_bound_client_ip


def normalize_hero_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", name.lower())


def _hero_list_payload() -> dict[str, Any]:
    return {
        "pageSize": 10000,
        "sorts": [
            {
                "data": {
                    "field": "hero_id",
                    "order": "desc",
                },
                "type": "sequence",
            }
        ],
        "pageIndex": 1,
        "fields": [
            "hero_id",
            "hero.data.head",
            "hero.data.name",
            "hero.data.smallmap",
        ],
    }


def get_hero_id_by_name(hero_name: str, lang: str = "en") -> int:
    # Bypass: Get hero ID from public endpoint
    url = "https://openmlbb.fastapicloud.dev/api/heroes"
    try:
        data = request_json(
            method="GET",
            url=url,
            headers=MLBBHeaderBuilder.get_academy_mlbb_header(lang, client_ip=get_bound_client_ip()),
            params={"size": 1000, "lang": lang}
        )
        search_name = normalize_hero_name(hero_name)
        for record in data.get("data", {}).get("records", []):
            hero_data = record.get("data", {}).get("hero", {}).get("data", {})
            if normalize_hero_name(hero_data.get("name", "")) == search_name:
                return int(record.get("data", {}).get("hero_id", 0))
    except Exception:
        pass
    return 0


def resolve_hero_id(hero_identifier: str, lang: str) -> int:
    try:
        return int(hero_identifier)
    except ValueError:
        return get_hero_id_by_name(hero_identifier, lang)


def fetch_mlbb_post(endpoint_id: str, payload: dict[str, Any], lang: str) -> Any:
    # Mapping table for internal MLBB IDs to public endpoints
    mapping = {
        "2756564": "heroes/positions",
        "2756567": "heroes/rank",
        "2756568": "heroes/rank",
        "2756569": "heroes/rank",
        "2756565": "heroes/rank",
        "2756570": "heroes/rank",
    }
    
    base_path = BasePathProvider.get_base_path()
    
    if base_path.startswith("http"):
        # Bypass mode (full URL fallback)
        path = mapping.get(endpoint_id, f"heroes/{endpoint_id}")
        url = f"{base_path}/{path}"
        
        # Determine method and params
        is_get = endpoint_id in ["2756564", "2756567", "2756568", "2756569", "2756565", "2756570"]
        method = "GET" if is_get else "POST"
        
        params = {"lang": lang}
        if is_get:
            params.update({
                "size": payload.get("pageSize", 20),
                "index": payload.get("pageIndex", 1),
            })
            
            # Handle rank, sort, role, and lane unmapping
            # The upstream API expects 'all' not '101', 'win_rate' not 'main_hero_win_rate', etc.
            rank_reverse = {"101": "all", "5": "epic", "6": "legend", "7": "mythic", "8": "honor", "9": "glory"}
            sort_reverse = {
                "main_hero_appearance_rate": "pick_rate",
                "main_hero_ban_rate": "ban_rate",
                "main_hero_win_rate": "win_rate"
            }
            role_reverse = {1: "tank", 2: "fighter", 3: "assassin", 4: "mage", 5: "marksman", 6: "support"}
            lane_reverse = {1: "exp", 2: "mid", 3: "roam", 4: "jungle", 5: "gold"}

            for f in payload.get("filters", []):
                field = f.get("field", "")
                value = f.get("value")
                
                if field == "bigrank":
                    params["rank"] = rank_reverse.get(str(value), value)
                elif "sortid" in field:
                    # Role filter
                    if isinstance(value, list):
                        params["role"] = [role_reverse.get(v, v) for v in value]
                    else:
                        params["role"] = role_reverse.get(value, value)
                elif "roadsort" in field:
                    # Lane filter
                    if isinstance(value, list):
                        params["lane"] = [lane_reverse.get(v, v) for v in value]
                    else:
                        params["lane"] = lane_reverse.get(value, value)
            
            for s in payload.get("sorts", []):
                if s.get("data", {}).get("field"):
                    params["sort_field"] = sort_reverse.get(s["data"]["field"], s["data"]["field"])
                    params["sort_order"] = s["data"].get("order", "desc")
                    
        return request_json(method=method, url=url, payload=payload if not is_get else None, params=params, headers=MLBBHeaderBuilder.get_academy_mlbb_header(lang, client_ip=get_bound_client_ip()))

    # Original mode
    url = f"{RONE_DEV_ACCESS_KEY}{base_path}/{endpoint_id}"
    headers = MLBBHeaderBuilder.get_academy_mlbb_header(lang, client_ip=get_bound_client_ip())
    return request_json(method="POST", url=url, payload=payload, headers=headers)
