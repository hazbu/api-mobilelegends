from __future__ import annotations

from typing import Any

from app.core.config import RONE_DEV_ACCESS_KEY, RONE_DEV_ACCESS_KEY_V2
from app.core.http import MLBBHeaderBuilder, request_json
from app.core.security import BasePathProvider
from app.utils.client_ip import get_bound_client_ip


def fetch_academy_post(endpoint_id: str, payload: dict[str, Any], lang: str) -> Any:
    # Mapping table for internal Academy IDs to public endpoints
    mapping = {
        "2718124": "academy/meta/version",
        "2766683": "academy/heroes/catalog",
        "2740642": "academy/roles",
        "2775075": "academy/equipment",
        "2713995": "academy/equipment/expanded",
        "2718122": "academy/spells",
        "2740638": "academy/emblems",
    }
    
    base_path = BasePathProvider.get_base_path_academy()
    
    if base_path.startswith("http"):
        # We are in bypass mode (using public URL)
        path = mapping.get(endpoint_id, f"academy/{endpoint_id}")
        url = f"{base_path}/{path}"
        # Academy public endpoints are mostly GET
        method = "GET"
        params = {"lang": lang, "size": payload.get("pageSize", 20), "index": payload.get("pageIndex", 1)}
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
