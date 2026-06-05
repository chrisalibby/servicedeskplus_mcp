def get_headers(api_key: str) -> dict[str, str]:
    return {
        "Authtoken": api_key,
        "Accept": "application/vnd.manageengine.sdp.v3+json",
    }
