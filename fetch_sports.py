import requests
import json
import time
from datetime import datetime, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://streamed.pk/",
    "Origin": "https://streamed.pk",
    "Accept": "application/json"
}

BASE_URL = "https://streamed.pk/api"

SPORT_ENDPOINTS = [
    "football", "cricket", "basketball", "tennis",
    "baseball", "hockey", "rugby", "golf", "mma", "boxing",
    "motorsport", "volleyball", "handball", "cycling", "other"
]

IMAGE_BASE = "https://streamed.pk"


def fetch_json(url, retries=3, delay=2):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=12)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError:
            print(f"  HTTP {r.status_code} -> {url}")
            if r.status_code == 429:
                time.sleep(delay * 2)
            break
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(delay)
    return None


def resolve_logo(raw):
    if not raw:
        return ""
    if raw.startswith("http"):
        return raw
    if raw.startswith("/"):
        return IMAGE_BASE + raw
    return raw


def extract_team(team_data):
    if not team_data:
        return {"name": "", "logo": ""}
    if isinstance(team_data, str):
        return {"name": team_data, "logo": ""}
    if isinstance(team_data, dict):
        name = (team_data.get("name") or team_data.get("title") or team_data.get("team") or "")
        logo = (team_data.get("badge") or team_data.get("logo") or
                team_data.get("image") or team_data.get("icon") or "")
        return {"name": str(name), "logo": resolve_logo(logo)}
    return {"name": "", "logo": ""}


def format_iso_time(raw_time):
    if not raw_time:
        return ""
    try:
        ts = int(raw_time)
        if ts > 1e10:
            ts = ts // 1000
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError):
        pass
    return str(raw_time)


def fetch_streams(match_id, sources):
    all_streams = []
    seen_urls = set()

    for src in sources:
        source_name = src.get("source", src) if isinstance(src, dict) else str(src)
        if not source_name:
            continue

        url = f"{BASE_URL}/stream/{source_name}/{match_id}"
        data = fetch_json(url)
        if not data:
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            embed_url = (item.get("embedUrl") or item.get("url") or item.get("link") or "")
            if not embed_url or embed_url in seen_urls:
                continue
            seen_urls.add(embed_url)
            all_streams.append({
                "source":   source_name,
                "embedUrl": embed_url,
                "language": item.get("language", item.get("lang", "en")),
                "hd":       bool(item.get("hd", item.get("isHD", False))),
                "quality":  "HD" if item.get("hd") else "SD"
            })
        time.sleep(0.3)

    return all_streams


def determine_status(match):
    override = match.get("_status_override", "")
    if override:
        return override
    if match.get("live") is True:
        return "LIVE"
    raw_status = str(match.get("status", "")).upper()
    if raw_status in ("LIVE", "INPROGRESS", "IN_PROGRESS", "ONGOING"):
        return "LIVE"
    if raw_status in ("UPCOMING", "SCHEDULED", "FIXTURE", "NS"):
        return "UPCOMING"
    if raw_status in ("ENDED", "FINISHED", "FT", "AET", "PEN", "COMPLETED"):
        return "ENDED"
    return "UPCOMING"


def fetch_all_matches():
    all_matches = []
    seen_ids = set()

    print("Live matches fetch korchi...")
    live_data = fetch_json(f"{BASE_URL}/matches/live")
    if live_data and isinstance(live_data, list):
        for m in live_data:
            m["_status_override"] = "LIVE"
            mid = m.get("id") or m.get("matchId")
            if mid and mid not in seen_ids:
                all_matches.append(m)
                seen_ids.add(mid)
        print(f"   {len([m for m in all_matches if m.get('_status_override') == 'LIVE'])} live match")

    for sport in SPORT_ENDPOINTS:
        print(f"{sport} fetch korchi...")
        data = fetch_json(f"{BASE_URL}/matches/{sport}")
        if data and isinstance(data, list):
            new_count = 0
            for m in data:
                mid = m.get("id") or m.get("matchId")
                if mid and mid not in seen_ids:
                    all_matches.append(m)
                    seen_ids.add(mid)
                    new_count += 1
            print(f"   {new_count} new match")
        time.sleep(0.5)

    return all_matches


def process_match(match):
    match_id = str(match.get("id") or match.get("matchId") or "")

    home_team = extract_team(match.get("home") or match.get("homeTeam") or match.get("team1"))
    away_team = extract_team(match.get("away") or match.get("awayTeam") or match.get("team2"))

    title = (
        match.get("title") or match.get("name") or match.get("event") or
        f"{home_team['name']} vs {away_team['name']}"
    ).strip()

    competition = (
        match.get("competition") or match.get("league") or
        match.get("tournament") or match.get("category") or match.get("sport") or ""
    )
    if isinstance(competition, dict):
        competition = competition.get("name", competition.get("title", ""))

    sport = match.get("sport") or match.get("category") or match.get("type") or ""
    if isinstance(sport, dict):
        sport = sport.get("name", "")

    raw_time = (
        match.get("date") or match.get("time") or match.get("startTime") or
        match.get("kickoff") or match.get("scheduled") or ""
    )
    match_time_utc = format_iso_time(raw_time)
    status = determine_status(match)
    sources = match.get("sources") or match.get("streams") or []
    streams = fetch_streams(match_id, sources) if match_id and sources else []
    poster = resolve_logo(
        match.get("poster") or match.get("image") or
        match.get("thumbnail") or match.get("banner") or ""
    )

    return {
        "id":          match_id,
        "title":       title,
        "sport":       str(sport).lower(),
        "competition": str(competition),
        "status":      status,
        "teams": {
            "home": home_team,
            "away": away_team
        },
        "matchTimeUTC": match_time_utc,
        "streams":      streams,
        "streamCount":  len(streams),
        "poster":       poster,
    }


def main():
    print("=" * 50)
    print("Sports Data Fetcher")
    print("=" * 50)
    start_time = time.time()

    raw_matches = fetch_all_matches()
    print(f"\nTotal {len(raw_matches)} matches found")
    print("Processing streams and team data...\n")

    processed = []
    for i, match in enumerate(raw_matches, 1):
        title = match.get("title") or match.get("name") or match.get("id") or "Unknown"
        print(f"  [{i:>3}/{len(raw_matches)}] {str(title)[:55]}")
        result = process_match(match)
        if result["status"] != "ENDED":
            processed.append(result)

    def sort_key(m):
        order = {"LIVE": 0, "UPCOMING": 1}.get(m["status"], 2)
        return (order, m.get("matchTimeUTC", ""))

    processed.sort(key=sort_key)
    elapsed = round(time.time() - start_time, 1)

    output = {
        "lastUpdated":   datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fetchDuration": f"{elapsed}s",
        "totalMatches":  len(processed),
        "liveCount":     sum(1 for m in processed if m["status"] == "LIVE"),
        "upcomingCount": sum(1 for m in processed if m["status"] == "UPCOMING"),
        "matches":       processed
    }

    with open("Sports_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 50}")
    print(f"Sports_data.json updated successfully!")
    print(f"  Live    : {output['liveCount']}")
    print(f"  Upcoming: {output['upcomingCount']}")
    print(f"  Total   : {output['totalMatches']}")
    print(f"  Time    : {elapsed}s")
    print("=" * 50)


if __name__ == "__main__":
    main()
