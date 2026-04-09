import json
import logging
import os
import time
import threading
from zoneinfo import ZoneInfo

import requests
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from twilio.rest import Client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

logger = logging.getLogger(__name__)

load_dotenv()

API_KEYS = os.getenv("API_KEYS").split(",")
API_HOST = os.getenv("API_HOST")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TWILIO_TO = os.getenv("TWILIO_TO")

@asynccontextmanager
async def lifespan(application: FastAPI):
    thread = threading.Thread(target=background_poller, daemon=True)
    thread.start()
    yield

app = FastAPI(title="Masters Leaderboard", lifespan=lifespan)

# --- Config ---
TOURNAMENT_URL = "https://golf-leaderboard-data.p.rapidapi.com/leaderboard/836"
POLL_INTERVAL_SECONDS = 180
PLAYERS_FILE = "players.json"


# --- State (in-memory, updated by background thread) ---
state = {
    "leaderboard": [],
    "tournament_leaderboard": [],
    "last_updated": None,
    "error": None,
}
api_call_count = 0


# --- API Key Rotation ---
def get_headers():
    """Rotate through API keys based on call count."""
    key = API_KEYS[api_call_count % len(API_KEYS)]
    return {
        "X-RapidAPI-Key": key,
        "X-RapidAPI-Host": API_HOST,
    }


# --- Load Players ---
def load_players():
    """Load player/golfer data from players.json."""
    with open(PLAYERS_FILE, "r") as f:
        data = json.load(f)
    return data["players"]


# --- Score Calculation ---
def calculate_player_scores(players, golfer_scores):
    """
    For each player, find their 6 golfers' scores, pick the best 3,
    and calculate tiebreakers.

    golfer_scores: dict of { "Full Name": {"score": int, "status": str} }
    """
    results = []

    for player in players:
        scores = []
        for golfer_name in player["golfers"]:
            golfer = golfer_scores.get(golfer_name)
            if golfer:
                scores.append({"name": golfer_name, "score": golfer["score"],
                               "status": golfer["status"]})  # CHANGED: added "name"

        # CHANGED: active_with_names keeps track of golfer names alongside scores
        active_with_names = sorted(
            [g for g in scores if g["status"].lower() in ("active", "complete", "not started", "notstarted")],
            key=lambda x: x["score"]
        )
        cut = sorted(
            [g["score"] for g in scores if g["status"].lower() in ("cut", "wd", "withdrawn", "dsq", "disqualified", "dq", "retired")]
        )

        active = [g["score"] for g in active_with_names]  # extract just scores from active_with_names

        top3_golfers = [{"name": g["name"], "score": g["score"]} for g in active_with_names[:3]]  # names and scores of the top 3 golfers
        bottom3_golfers = [{"name": g["name"], "score": g["score"]} for g in active_with_names[3:]]

        all_golfers = (
                [{"name": g["name"], "score": g["score"], "status": g["status"], "counts": True} for g in
                 active_with_names[:3]] +
                [{"name": g["name"], "score": g["score"], "status": g["status"], "counts": False} for g in
                 active_with_names[3:]] +
                [{"name": g["name"], "score": g["score"], "status": g["status"], "counts": False} for g in scores if
                 g["status"].lower() in ("cut", "wd", "withdrawn", "dsq", "dq", "disqualified", "retired")]
        )

        if len(active) < 3:
            results.append({
                "name": player["name"],
                "score": float("inf"),
                "display_score": "Missed Cut",
                "top3_golfers": top3_golfers,  # NEW
                "bottom3_golfers": bottom3_golfers,
                "golfers": all_golfers,
                "tiebreak_1": 0,
                "tiebreak_2": float("inf"),
                "tiebreak_3": float("inf"),
                "tiebreak_4": float("inf"),
            })
            continue

        top3 = sum(active[:3])
        tb1 = len(active)

        if len(active) >= 4:
            tb2 = sum(active[:4])
        elif cut:
            tb2 = sum(active) + cut[0]
        else:
            tb2 = float("inf")

        if len(active) >= 5:
            tb3 = sum(active[:5])
        elif len(active) == 4 and cut:
            tb3 = sum(active) + cut[0]
        elif len(active) == 3 and len(cut) >= 2:
            tb3 = sum(active) + cut[0] + cut[1]
        else:
            tb3 = float("inf")

        if len(active) == 6:
            tb4 = sum(active)
        elif cut:
            tb4 = sum(active) + sum(cut)
        else:
            tb4 = float("inf")

        results.append({
            "name": player["name"],
            "score": top3,
            "display_score": f"{top3:+d}" if top3 != 0 else "E",
            "top3_golfers": top3_golfers,  # NEW
            "bottom3_golfers": bottom3_golfers,
            "golfers": all_golfers,
            "tiebreak_1": tb1,
            "tiebreak_2": tb2,
            "tiebreak_3": tb3,
            "tiebreak_4": tb4,
        })

    results.sort(key=lambda x: (
        x["score"],
        -x["tiebreak_1"],
        x["tiebreak_2"],
        x["tiebreak_3"],
        x["tiebreak_4"],
    ))

    for i, player in enumerate(results):
        if i == 0 or player["score"] != results[i - 1]["score"]:
            player["position"] = i + 1
        else:
            player["position"] = results[i - 1]["position"]

    return results

def send_error_sms(error_message):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=f"Masters Leaderboard error: {error_message}",
            from_=f"whatsapp:{TWILIO_FROM}",
            to=f"whatsapp:{TWILIO_TO}"
        )
        logger.info("Error Whatsapp message sent.")
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        print(f"Failed to send Whatsapp message: {e}")


# --- Fetch & Update ---
def fetch_and_update():
    """Fetch latest golf scores and update the leaderboard."""
    global api_call_count

    last_error = None
    for attempt in range(len(API_KEYS)):
        try:
            response = requests.get(TOURNAMENT_URL, headers=get_headers(), timeout=10)
            response.raise_for_status()
            api_call_count += 1
            break  #successfull api call - stop trying

        except Exception as e:
            last_error = e
            logger.warning(f"API Key ending...{API_KEYS[api_call_count % len(API_KEYS)][-6:]} failed: {e}, trying next key...")
            api_call_count += 1
            continue

    else:
        # All keys failed
        state["error"] = str(last_error)
        logger.error(f"All API keys failed: {last_error}")
        send_error_sms(f"All API keys failed: {last_error}")
        return

    try:
        leaderboard_data = response.json()["results"]["leaderboard"]

        # Build a lookup dict: "First Last" -> {score, status}
        golfer_scores = {}
        for golfer in leaderboard_data:
            name = f"{golfer['first_name']} {golfer['last_name']}"
            golfer_scores[name] = {
                "score": golfer["total_to_par"],
                "status": golfer["status"],
            }

        players = load_players()
        leaderboard = calculate_player_scores(players, golfer_scores)

        state["leaderboard"] = leaderboard
        state["last_updated"] = datetime.now().strftime("%H:%M:%S")
        state["error"] = None
        state["tournament_leaderboard"] = [
            {
                "name": f"{g['first_name']} {g['last_name']}",
                "score": g["total_to_par"],
                "display_score": f"{g['total_to_par']:+d}" if g["total_to_par"] != 0 else "E",
                "status": g["status"],
                "position": g.get("position", 0),
                "current_round": g.get("current_round", 0),
                "holes_played": g.get("holes_played", 0),
                "rounds": g.get("rounds", []),
            }
            for g in leaderboard_data
        ]

        logger.info(f"[{state['last_updated']}] Leaderboard updated. API calls: {api_call_count}")

    except Exception as e:
        state["error"] = str(e)
        logger.error(f"Error fetching leaderboard: {e}")
        send_error_sms(str(e))

def is_within_polling_window():
    """Only poll during Masters playing hours (ET)."""
    # TODO: Verify the start times and likely finish times of each round
    et = ZoneInfo("America/New_York")
    now = datetime.now(et)

    # Masters dates 2026
    tournament_days = {
        9:  {"start": 8,  "start_min": 5},   # Thursday  - first tee time ~8:00am, start polling 8:05am
        10: {"start": 8,  "start_min": 5},   # Friday    - first tee time ~8:00am, start polling 8:05am
        11: {"start": 10, "start_min": 5},   # Saturday  - first tee time ~10:00am, start polling 10:05am
        12: {"start": 10, "start_min": 5},   # Sunday    - first tee time ~10:00am, start polling 10:05am
    }

    # Only run in April 2026
    if now.year != 2026 or now.month != 4:
        return False

    day = now.day
    if day not in tournament_days:
        return False

    window = tournament_days[day]
    start = now.replace(hour=window["start"], minute=window["start_min"], second=0)
    end   = now.replace(hour=19, minute=0, second=0)  # 7:00pm ET

    return start <= now <= end

def background_poller():
    """Runs in a background thread, polling every POLL_INTERVAL_SECONDS."""
    while True:
        # Uncomment the block below when ready for the actual tournament:
        # if is_within_polling_window():
        #     fetch_and_update()
        # else:
        #     logger.info("Outside polling window, skipping.")
        #     print("Outside polling window, skipping.")

        # Remove the line below (fetch_and_update()) when uncommenting the block above - keep the sleep interval:
        fetch_and_update()
        time.sleep(POLL_INTERVAL_SECONDS)


# --- API Routes ---
@app.get("/api/leaderboard")
def get_leaderboard():
    # Replace any float('inf') with None so it's JSON-safe
    clean_leaderboard = []
    for player in state["leaderboard"]:
        clean_player = {
            k: (None if isinstance(v, float) and v == float("inf") else v)
            for k, v in player.items()
        }
        clean_leaderboard.append(clean_player)

    return {
        "leaderboard": clean_leaderboard,
        "last_updated": state["last_updated"],
        "error": state["error"],
    }

@app.get("/api/refresh")
def manual_refresh():
    """Manually trigger a leaderboard refresh."""
    fetch_and_update()
    return {"status": "refreshed", "last_updated": state["last_updated"]}

@app.get("/api/tournament")
def get_tournament_leaderboard():
    return {
        "leaderboard": state["tournament_leaderboard"],
        "last_updated": state["last_updated"],
        "error": state["error"],
    }

@app.get("/tournament")
def serve_tournament():
    return FileResponse("static/tournament.html")

# --- Serve frontend ---
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")
