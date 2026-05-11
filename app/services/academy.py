from __future__ import annotations

from typing import Any

from app.core.config import RONE_DEV_ACCESS_KEY, RONE_DEV_ACCESS_KEY_V2
from app.core.http import MLBBHeaderBuilder, request_json
from app.core.security import BasePathProvider
from app.utils.client_ip import get_bound_client_ip


_RANK_REVERSE_MAP = {
    "101": "all",
    "5": "epic",
    "6": "legend",
    "7": "mythic",
    "8": "honor",
    "9": "glory",
}

_ROLE_REVERSE_MAP = {
    1: "tank",
    2: "fighter",
    3: "assassin",
    4: "mage",
    5: "marksman",
    6: "support",
}

_LANE_REVERSE_MAP = {
    1: "exp",
    2: "mid",
    3: "roam",
    4: "jungle",
    5: "gold",
}

_TREND_DAY_ID_MAP = {
    "2755185": "7",
    "2755186": "15",
    "2755187": "30",
}


def _find_filter_value(payload: dict[str, Any], field: str) -> Any:
    for item in payload.get("filters", []):
        if item.get("field") == field:
            return item.get("value")
    return None


def _find_sort_order(payload: dict[str, Any]) -> Any:
    for item in payload.get("sorts", []):
        order = item.get("data", {}).get("order")
        if order:
            return order
    return None


def _map_multi_value(value: Any, mapping: dict[int, str]) -> Any:
    if isinstance(value, list):
        return [mapping.get(int(v), v) if str(v).isdigit() else mapping.get(v, v) for v in value]
    if value is None:
        return None
    return mapping.get(int(value), value) if str(value).isdigit() else mapping.get(value, value)


def _resolve_bypass_path(endpoint_id: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    path = {
        "2718124": "academy/meta/version",
        "2766683": "academy/heroes/catalog",
        "2740642": "academy/roles",
        "2775075": "academy/equipment",
        "2713995": "academy/equipment/expanded",
        "2718122": "academy/spells",
        "2740638": "academy/emblems",
        "2718121": "academy/emblems",
        "3210596": "academy/ranks",
        "2755183": "academy/heroes/{hero_id}/stats",
        "2777027": "academy/heroes/{hero_id}/win-rate/timeline",
        "2776688": "academy/heroes/{hero_id}/builds",
        "2777391": "academy/heroes/{hero_id}/counters",
        "2755185": "academy/heroes/{hero_id}/trends",
        "2755186": "academy/heroes/{hero_id}/trends",
        "2755187": "academy/heroes/{hero_id}/trends",
    }.get(endpoint_id, f"academy/{endpoint_id}")

    hero_id = (
        _find_filter_value(payload, "main_heroid")
        or _find_filter_value(payload, "hero_id")
        or _find_filter_value(payload, "heroid")
        or _find_filter_value(payload, "data.data.hero.hero_id")
    )
    form_id = _find_filter_value(payload, "formId")
    recommended_id = _find_filter_value(payload, "id")
    camp_type = _find_filter_value(payload, "camp_type")
    rank_id = _find_filter_value(payload, "rankid_start")
    fields = payload.get("fields", [])
    meta: dict[str, Any] = {
        "hero_id": hero_id,
        "recommended_id": recommended_id,
        "rank_id": rank_id,
    }

    if endpoint_id == "2718124":
        if form_id == 2737553 and recommended_id is not None:
            path = "academy/recommended/{recommended_id}"
        elif form_id == 2737553 and hero_id is not None:
            path = "academy/heroes/{hero_id}/recommended"
        elif form_id == 2737553:
            path = "academy/recommended"
        else:
            path = "academy/meta/version"

    elif endpoint_id == "2766683":
        if hero_id is not None and "hero.data.roadsort" in fields:
            path = "academy/heroes/{hero_id}/lane"
        elif "head_big" in fields or "painting" in fields or payload.get("object") == [2667538]:
            path = "academy/heroes/catalog"
        else:
            path = "academy/heroes"

    elif endpoint_id == "3210596":
        rank_end_id = _find_filter_value(payload, "rankid_end")
        if rank_id is not None and rank_end_id == rank_id:
            path = "academy/ranks/{rank_id}"
        else:
            path = "academy/ranks"

    elif endpoint_id == "2777391":
        path = "academy/heroes/{hero_id}/teammates" if str(camp_type) == "1" else "academy/heroes/{hero_id}/counters"

    if "{hero_id}" in path:
        path = path.format(hero_id=hero_id if hero_id is not None else 0)
    if "{recommended_id}" in path:
        path = path.format(recommended_id=recommended_id if recommended_id is not None else 0)
    if "{rank_id}" in path:
        path = path.format(rank_id=rank_id if rank_id is not None else 0)

    return path, meta


def _build_bypass_params(endpoint_id: str, payload: dict[str, Any], lang: str) -> dict[str, Any]:
    params: dict[str, Any] = {
        "lang": lang,
        "size": payload.get("pageSize", 20),
        "index": payload.get("pageIndex", 1),
    }

    order = _find_sort_order(payload)
    if order:
        params["order"] = order

    rank_value = _find_filter_value(payload, "bigrank") or _find_filter_value(payload, "big_rank")
    if rank_value is not None:
        params["rank"] = _RANK_REVERSE_MAP.get(str(rank_value), rank_value)

    lane_value = _find_filter_value(payload, "real_road")
    if lane_value is not None:
        params["lane"] = _LANE_REVERSE_MAP.get(int(lane_value), lane_value) if str(lane_value).isdigit() else lane_value

    role_values = _find_filter_value(payload, "<hero.data.sortid>")
    if role_values is not None:
        params["role"] = _map_multi_value(role_values, _ROLE_REVERSE_MAP)

    hero_lane_values = _find_filter_value(payload, "<hero.data.roadsort>")
    if hero_lane_values is not None:
        params["lane"] = _map_multi_value(hero_lane_values, _LANE_REVERSE_MAP)

    if endpoint_id in _TREND_DAY_ID_MAP:
        params["days"] = _TREND_DAY_ID_MAP[endpoint_id]

    return params


def fetch_academy_post(endpoint_id: str, payload: dict[str, Any], lang: str) -> Any:
    base_path = BasePathProvider.get_base_path_academy()
    
    if base_path.startswith("http"):
        # We are in bypass mode (using public URL)
        path, _ = _resolve_bypass_path(endpoint_id, payload)
        url = f"{base_path}/{path}"
        method = "GET"
        params = _build_bypass_params(endpoint_id, payload, lang)
        return request_json(method=method, url=url, params=params, headers=MLBBHeaderBuilder.get_academy_mlbb_header(lang, client_ip=get_bound_client_ip()))
    
    url = f"{RONE_DEV_ACCESS_KEY}{base_path}/{endpoint_id}"
    headers = MLBBHeaderBuilder.get_academy_mlbb_header(lang, client_ip=get_bound_client_ip())
    return request_json(method="POST", url=url, payload=payload, headers=headers)


def fetch_ratings_all(lang: str) -> Any:
    base_path = BasePathProvider.get_base_path_ratings()
    url = f"{RONE_DEV_ACCESS_KEY_V2}{base_path}?offset=0"
    headers = MLBBHeaderBuilder.get_academy_mlbb_header(lang, client_ip=get_bound_client_ip())
    return request_json(method="GET", url=url, headers=headers)


def fetch_ratings_subject(lang: str, subject: str) -> Any:
    base_path = BasePathProvider.get_base_path_ratings()
    url = f"{RONE_DEV_ACCESS_KEY_V2}{base_path}/{subject}"
    headers = MLBBHeaderBuilder.get_academy_mlbb_header(lang, client_ip=get_bound_client_ip())
    return request_json(method="GET", url=url, headers=headers)
