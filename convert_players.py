"""
convert_players.py

Converts a CSV file of player picks into players.json.

CSV format:
    name,golfer1,golfer2,golfer3,golfer4,golfer5,golfer6
    P. Greenwell,Rory McIlroy,Scottie Scheffler,Jon Rahm,Brooks Koepka,Justin Thomas,Xander Schauffele

Usage:
    python convert_players.py                        # uses players.csv by default
    python convert_players.py my_picks.csv           # specify a custom CSV file
"""

import csv
import json
import sys
import os


def convert(csv_path="players.csv", json_path="players.json"):
    if not os.path.exists(csv_path):
        print(f"Error: '{csv_path}' not found.")
        sys.exit(1)

    players = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("name", "").strip()
            if not name:
                continue

            golfers = [
                row.get(f"golfer{i}", "").strip()
                for i in range(1, 7)
                if row.get(f"golfer{i}", "").strip()
            ]

            if len(golfers) != 6:
                print(f"Warning: '{name}' has {len(golfers)} golfers, expected 6. Skipping.")
                continue

            players.append({"name": name, "golfers": golfers})

    if not players:
        print("No valid players found in CSV. Check the format and try again.")
        sys.exit(1)

    output = {"players": players}

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Converted {len(players)} players from '{csv_path}' to '{json_path}'.")


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "players.csv"
    convert(csv_path=csv_file)