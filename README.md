## Disclaimer

This project fetches publicly available data from third-party APIs
for informational and educational purposes only.

- This project does not host, store, or distribute any media content.
- All stream links and match data belong to their respective owners.
- If you are a rights holder and want data removed, contact: safikm34@gmail.com

# Live Sports Data

Automatically fetches live & upcoming sports matches with stream links, team info, and competition details — updated every hour via GitHub Actions.

## JSON URL

```
https://raw.githubusercontent.com/shafik4bd/upcoming-and-live-sports-data-api/main/Sports_data.json
```

## Data Source

- **Not Mentioned** — No API key required

## JSON Structure

```json
{
  "lastUpdated": "2026-06-08T14:00:00Z",
  "fetchDuration": "42s",
  "totalMatches": 23,
  "liveCount": 5,
  "upcomingCount": 18,
  "matches": [
    {
      "id": "abc123",
      "title": "Manchester City vs Arsenal",
      "sport": "football",
      "competition": "Premier League",
      "status": "LIVE",
      "matchTimeUTC": "2026-06-08T14:00:00Z",
      "teams": {
        "home": { "name": "Manchester City", "logo": "https://…" },
        "away": { "name": "Arsenal",         "logo": "https://…" }
      },
      "streams": [
        { "source": "alpha", "embedUrl": "https://…", "language": "en", "hd": true,  "quality": "HD" },
        { "source": "bravo", "embedUrl": "https://…", "language": "en", "hd": false, "quality": "SD" }
      ],
      "streamCount": 2,
      "poster": "https://…/poster.jpg"
    }
  ]
}
```

## Setup

1. Fork or clone this repo
2. Go to **Settings → Actions → General**
3. Set **Workflow permissions** → Read and write permissions
4. Run manually: **Actions → Update Sports Data → Run workflow**

Runs automatically every hour after first manual trigger.

## Note

For educational purposes only. Content may be geo-restricted to Bangladesh.
