# Masters Fantasy Leaderboard

A FastAPI web app that pulls live Masters golf scores and ranks your fantasy pool players.

---

## Project Structure

```
masters-leaderboard/
├── main.py              # FastAPI app — all backend logic lives here
├── players.json         # Your players and their 6 golfer picks
├── requirements.txt     # Python dependencies
├── Procfile             # Tells Railway how to start the app
├── static/
│   └── index.html       # The frontend (auto-refreshes every 2 mins)
└── test_leaderboard.py  # Unit tests
```

---

## Before the Tournament: Fill in players.json

Edit `players.json` with your actual players and their golfer selections.
Golfer names **must match exactly** how they appear in the RapidAPI response
(usually `"First Last"` format, e.g. `"Rory McIlroy"`).

```json
{
  "players": [
    {
      "name": "Your Name",
      "golfers": [
        "Golfer One",
        "Golfer Two",
        "Golfer Three",
        "Golfer Four",
        "Golfer Five",
        "Golfer Six"
      ]
    }
  ]
}
```

---

## Running Locally

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the server
```bash
uvicorn main:app --reload
```

### 3. Open your browser
Go to: http://localhost:8000

---

## Adding / Rotating API Keys

Store multiple API_KEYS in a .env file.

Keys are rotated automatically on each API call (round-robin).

---

## How Scoring Works

1. Each player picks **6 golfers**
2. Their score = the **best 3 active golfers'** combined scores (to par)
3. If a player has fewer than 3 active golfers (all others missed the cut), they are shown as **Missed Cut**

### Tiebreakers (in order)
| # | Rule |
|---|------|
| 1 | More active golfers still in the tournament = better |
| 2 | Best 4 combined scores |
| 3 | Best 5 combined scores |
| 4 | All 6 combined scores |

---

## Running Tests
```bash
python -m pytest test_leaderboard.py -v
```

---

## Updating for Next Year

1. Update `players.json` with new player/golfer selections
2. Update the tournament ID in `main.py`:
   ```python
   TOURNAMENT_URL = "https://golf-leaderboard-data.p.rapidapi.com/leaderboard/NEW_ID"
   ```
3. Redeploy to Railway (just push to GitHub — it auto-deploys)
