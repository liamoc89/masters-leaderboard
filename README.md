# Masters Fantasy Leaderboard

A FastAPI web app that pulls live Masters golf scores and ranks your fantasy pool players.

---

## Project Structure

```
masters-leaderboard/
├── main.py                 # FastAPI app — all backend logic lives here
├── players.json            # Your players and their 6 golfer picks (not committed to GitHub)
├── players.csv             # Optional — fill this in and run convert_players.py to generate players.json
├── players_template.csv    # Blank CSV template to fill in with player picks
├── convert_players.py      # Converts players.csv to players.json
├── requirements.txt        # Python dependencies
├── Procfile                # Tells your hosting provider how to start the app
├── .env                    # Local environment variables (not committed to GitHub)
├── .gitignore              # Excludes .env, players.json, .venv, .idea etc from GitHub
├── static/
│   └── index.html          # The frontend (auto-refreshes every 3 mins)
└── test_leaderboard.py     # Unit tests
```

---

## Environment Variables

The app requires the following environment variables. Locally these live in a `.env` file. On your hosting provider they should be set as environment variables in whatever way that platform supports.

| Variable | Description |
|---|---|
| `API_KEYS` | Comma-separated RapidAPI keys e.g. `key1,key2,key3,key4` |
| `API_HOST` | RapidAPI host — `golf-leaderboard-data.p.rapidapi.com` |
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token |
| `TWILIO_FROM` | Your Twilio phone number e.g. `+1234567890` |
| `TWILIO_TO` | Your mobile number to receive error alerts e.g. `+447xxxxxxxxx` |

### Example .env file
```
API_KEYS=key1,key2,key3,key4
API_HOST=golf-leaderboard-data.p.rapidapi.com
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM=+1234567890
TWILIO_TO=+447xxxxxxxxx
```

---

## Before the Tournament: Fill in players.json

There are two ways to set up your player data:

### Option 1 — CSV (recommended)

Fill in `players_template.csv` with your player names and golfer picks, save it as `players.csv`, then run:

```bash
python convert_players.py
```

This generates `players.json` automatically. The CSV format is:

```
name,golfer1,golfer2,golfer3,golfer4,golfer5,golfer6
P. Greenwell,Rory McIlroy,Scottie Scheffler,Jon Rahm,Brooks Koepka,Justin Thomas,Xander Schauffele
D. Gorley,Tiger Woods,Dustin Johnson,Collin Morikawa,Will Zalatoris,Cameron Smith,Tony Finau
```

You can also specify a custom CSV filename:

```bash
python convert_players.py my_picks.csv
```

### Option 2 — Edit players.json directly

Edit `players.json` manually with your actual players and their golfer selections.

### Important: Golfer names must match the API

Golfer names **must match exactly** how they appear in the RapidAPI response (usually `"First Last"` format, e.g. `"Rory McIlroy"`).

To verify golfer names, run the following in a Jupyter notebook once the field is announced:

```python
import requests

url = "https://golf-leaderboard-data.p.rapidapi.com/leaderboard/TOURNAMENT_ID"
headers = {
    "x-rapidapi-key": "your-key-here",
    "x-rapidapi-host": "golf-leaderboard-data.p.rapidapi.com"
}
response = requests.get(url, headers=headers)
for golfer in response.json()["results"]["leaderboard"]:
    print(golfer["first_name"], golfer["last_name"])
```

### players.json format
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

## Finding the Tournament ID

Run the following in a Jupyter notebook to get a list of all 2026 PGA Tour tournaments and their IDs:

```python
import requests

url = "https://golf-leaderboard-data.p.rapidapi.com/fixtures/2/2026"
headers = {
    "x-rapidapi-key": "your-key-here",
    "x-rapidapi-host": "golf-leaderboard-data.p.rapidapi.com"
}
response = requests.get(url, headers=headers)
for tournament in response.json()["results"]:
    print(tournament["id"], "-", tournament["name"])
```

Then update `TOURNAMENT_URL` in `main.py`:
```python
TOURNAMENT_URL = "https://golf-leaderboard-data.p.rapidapi.com/leaderboard/YOUR_ID"
```

**2026 Masters Tournament ID: 837**

---

## Running Locally

### 1. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create your .env file
Copy the example above and fill in your values.

### 4. Start the server
```bash
uvicorn main:app --reload
```

### 5. Open your browser
Go to: http://localhost:8000

---

## API Key Rotation

The app automatically rotates through your API keys on each poll using round-robin. With 4 keys and a 3 minute polling interval, each key is used roughly once every 12 minutes.

Keys are stored as a comma-separated list in the `API_KEYS` environment variable:
```
API_KEYS=key1,key2,key3,key4
```

---

## API Usage Budget

The RapidAPI basic plan allows ~250 requests per month per key. With 4 keys that's ~1000 requests total.

The Masters runs over 4 days with the following polling windows:

| Day | Start | End | Duration |
|---|---|---|---|
| Thursday | 8:05am ET | 7:00pm ET | 655 mins |
| Friday | 8:05am ET | 7:00pm ET | 655 mins |
| Saturday | 10:05am ET | 7:00pm ET | 535 mins |
| Sunday | 10:05am ET | 7:00pm ET | 535 mins |
| **Total** | | | **2380 mins** |

At a 3 minute polling interval this uses ~793 requests — safely within the ~900 request budget (leaving room for testing and manual refreshes).

---

## Polling Window

During the actual tournament, the app only polls the API during playing hours. This is controlled by the `is_within_polling_window()` function in `main.py`.

To enable this, uncomment the polling window block in `background_poller()` and comment out the always-on `fetch_and_update()` call:

```python
def background_poller():
    while True:
        if is_within_polling_window():
            fetch_and_update()
        else:
            print("Outside polling window, skipping.")
        time.sleep(POLL_INTERVAL_SECONDS)
```

---

## Error Alerts

If an API call fails, the app sends an SMS via Twilio to the number specified in `TWILIO_TO`. This requires a Twilio account with a valid phone number.

---

## How Scoring Works

1. Each player picks **6 golfers**
2. Their score = the **best 3 active golfers'** combined scores (to par)
3. A golfer counts as active if their status is `active`, `complete`, or `not started`
4. A golfer counts as cut if their status is `cut`, `wd`, `withdrawn`, `dsq`, `disqualified`, `dq`, or `retired`
5. If a player has fewer than 3 active golfers, they are shown as **Missed Cut**

### Tiebreakers (in order)
| # | Rule |
|---|---|
| 1 | More active golfers still in the tournament = better |
| 2 | Best 4 combined scores (active golfers first, then best cut score if needed) |
| 3 | Best 5 combined scores (active golfers first, then best cut scores if needed) |
| 4 | All 6 combined scores |

---

## Running Tests
```bash
python -m unittest test_leaderboard -v
```

---

## Deploying

The app can be hosted on any platform that supports Python and can run a `uvicorn` process. The `Procfile` contains the startup command:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Make sure to set all environment variables listed above on your hosting platform before deploying.

---

## Updating for Next Year

1. Update `players.json` with new player/golfer selections
2. Find the new Masters tournament ID using the fixtures endpoint above
3. Update `TOURNAMENT_URL` in `main.py` with the new ID
4. Update the tournament dates in `is_within_polling_window()` in `main.py`
5. Redeploy