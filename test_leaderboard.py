import unittest
from main import calculate_player_scores


class TestLeaderboard(unittest.TestCase):

    def setUp(self):
        """Sample players used across tests."""
        self.players = [
            {"name": "P. Greenwell", "golfers": ["playerA", "playerB", "playerC", "playerD", "playerE", "playerF"]},
            {"name": "D. Gorley",    "golfers": ["playerA", "playerB", "playerC", "playerD", "playerE", "playerF"]},
            {"name": "D. Elder",     "golfers": ["playerA", "playerB", "playerC", "playerD", "playerE", "playerF"]},
            {"name": "T. Moore",     "golfers": ["playerA", "playerB", "playerC", "playerD", "playerE", "playerF"]},
        ]

    def test_basic_scoring(self):
        """Top 3 active scores should be summed for each player's score."""
        golfer_scores = {
            "playerA": {"score": -12, "status": "active"},
            "playerB": {"score": -11, "status": "active"},
            "playerC": {"score": -4,  "status": "active"},
            "playerD": {"score":  7,  "status": "active"},
            "playerE": {"score":  4,  "status": "active"},
            "playerF": {"score":  3,  "status": "active"},
        }
        players = [{"name": "P. Greenwell", "golfers": ["playerA", "playerB", "playerC", "playerD", "playerE", "playerF"]}]
        result = calculate_player_scores(players, golfer_scores)
        # Best 3: -12, -11, -4 = -27
        self.assertEqual(result[0]["score"], -27)

    def test_missed_cut(self):
        """Player with fewer than 3 active golfers should be marked Missed Cut."""
        golfer_scores = {
            "playerA": {"score": -10, "status": "active"},
            "playerB": {"score": -11, "status": "cut"},
            "playerC": {"score": -4,  "status": "cut"},
            "playerD": {"score":  5,  "status": "cut"},
            "playerE": {"score":  7,  "status": "cut"},
            "playerF": {"score": 13,  "status": "cut"},
        }
        players = [{"name": "D. Gorley", "golfers": ["playerA", "playerB", "playerC", "playerD", "playerE", "playerF"]}]
        result = calculate_player_scores(players, golfer_scores)
        self.assertEqual(result[0]["display_score"], "Missed Cut")

    def test_sort_order(self):
        """Lower score should rank higher."""
        golfer_scores = {
            "playerA": {"score": -12, "status": "active"},
            "playerB": {"score": -11, "status": "active"},
            "playerC": {"score": -4,  "status": "active"},
            "playerD": {"score":  5,  "status": "active"},
            "playerE": {"score":  3,  "status": "active"},
            "playerF": {"score":  7,  "status": "active"},
        }
        players = [
            {"name": "P. Greenwell", "golfers": ["playerA", "playerB", "playerC", "playerD", "playerE", "playerF"]},
            {"name": "T. Moore",     "golfers": ["playerA", "playerB", "playerD", "playerC", "playerE", "playerF"]},
        ]
        result = calculate_player_scores(players, golfer_scores)
        # Both have same golfers so same score — just check no crash
        self.assertEqual(result[0]["position"], 1)

    def test_missed_cut_goes_to_bottom(self):
        """Missed cut players should always be ranked below active players."""
        golfer_scores = {
            "playerA": {"score": -10, "status": "active"},
            "playerB": {"score": -9,  "status": "active"},
            "playerC": {"score": -8,  "status": "active"},
            "playerD": {"score":  5,  "status": "cut"},
            "playerE": {"score":  7,  "status": "cut"},
            "playerF": {"score": 13,  "status": "cut"},
        }
        players = [
            {"name": "Active Player", "golfers": ["playerA", "playerB", "playerC", "playerD", "playerE", "playerF"]},
            {"name": "Cut Player",    "golfers": ["playerD", "playerE", "playerF", "playerD", "playerE", "playerF"]},
        ]
        result = calculate_player_scores(players, golfer_scores)
        names = [p["name"] for p in result]
        self.assertEqual(names[0], "Active Player")
        self.assertEqual(names[-1], "Cut Player")

    def test_tiebreaker_ordering(self):
        """
        All 5 players tied at -20.
        Tiebreak 1: most active golfers (players 1,2,3 have 4; players 4,5 have 3)
        Tiebreak 2: best 4 scores (player 3 drops behind 1 and 2; player 4 beats player 5)
        Tiebreak 3: best 5 scores (player 2 beats player 1)
        Expected order: player2, player1, player3, player4, player5
        """
        players = [
            {
                "name": "Player1",
                "golfers": ["p1g1", "p1g2", "p1g3", "p1g4", "p1g5", "p1g6"]
            },
            {
                "name": "Player2",
                "golfers": ["p2g1", "p2g2", "p2g3", "p2g4", "p2g5", "p2g6"]
            },
            {
                "name": "Player3",
                "golfers": ["p3g1", "p3g2", "p3g3", "p3g4", "p3g5", "p3g6"]
            },
            {
                "name": "Player4",
                "golfers": ["p4g1", "p4g2", "p4g3", "p4g4", "p4g5", "p4g6"]
            },
            {
                "name": "Player5",
                "golfers": ["p5g1", "p5g2", "p5g3", "p5g4", "p5g5", "p5g6"]
            },
        ]

        golfer_scores = {
            # Player 1 — 4 active, 2 cut. Best 3 = -20, 4th = -3, 5th = +5, 6th = 0 (cut)
            "p1g1": {"score": -8,  "status": "active"},
            "p1g2": {"score": -7,  "status": "active"},
            "p1g3": {"score": -5,  "status": "active"},
            "p1g4": {"score": -3,  "status": "active"},
            "p1g5": {"score":  5,  "status": "cut"},
            "p1g6": {"score":  0,  "status": "cut"},

            # Player 2 — 4 active, 2 cut. Best 3 = -20, 4th = -3, 5th = +4, 6th = 0 (cut)
            "p2g1": {"score": -8,  "status": "active"},
            "p2g2": {"score": -7,  "status": "active"},
            "p2g3": {"score": -5,  "status": "active"},
            "p2g4": {"score": -3,  "status": "active"},
            "p2g5": {"score":  4,  "status": "cut"},
            "p2g6": {"score":  0,  "status": "cut"},

            # Player 3 — 4 active, 2 cut. Best 3 = -20, 4th = -2, 5th = +1, 6th = 0 (cut)
            "p3g1": {"score": -8,  "status": "active"},
            "p3g2": {"score": -7,  "status": "active"},
            "p3g3": {"score": -5,  "status": "active"},
            "p3g4": {"score": -2,  "status": "active"},
            "p3g5": {"score":  1,  "status": "cut"},
            "p3g6": {"score":  0,  "status": "cut"},

            # Player 4 — 3 active, 3 cut. Best 3 = -20, 4th (best cut) = +1, 5th = 0, 6th = 0
            "p4g1": {"score": -8,  "status": "active"},
            "p4g2": {"score": -7,  "status": "active"},
            "p4g3": {"score": -5,  "status": "active"},
            "p4g4": {"score":  1,  "status": "cut"},
            "p4g5": {"score":  0,  "status": "cut"},
            "p4g6": {"score":  0,  "status": "cut"},

            # Player 5 — 3 active, 3 cut. Best 3 = -20, 4th (best cut) = +2, 5th = 0, 6th = 0
            "p5g1": {"score": -8,  "status": "active"},
            "p5g2": {"score": -7,  "status": "active"},
            "p5g3": {"score": -5,  "status": "active"},
            "p5g4": {"score":  2,  "status": "cut"},
            "p5g5": {"score":  0,  "status": "cut"},
            "p5g6": {"score":  0,  "status": "cut"},
        }

        result = calculate_player_scores(players, golfer_scores)
        names = [p["name"] for p in result]
        self.assertEqual(names, ["Player2", "Player1", "Player3", "Player4", "Player5"])

    def test_more_active_golfers_always_ranks_higher(self):
        """
        Player A has 4 active golfers, Player B has 3.
        Despite Player B having a better tb3 score, Player A should always rank higher
        due to having more active golfers.
        """
        players = [
            {
                "name": "PlayerA",
                "golfers": ["pag1", "pag2", "pag3", "pag4", "pag5", "pag6"]
            },
            {
                "name": "PlayerB",
                "golfers": ["pbg1", "pbg2", "pbg3", "pbg4", "pbg5", "pbg6"]
            },
        ]

        golfer_scores = {
            # Player A — 4 active. Best 3 = -20, 4th = -3, 5th = +5 (cut), 6th = 0 (cut)
            "pag1": {"score": -8, "status": "active"},
            "pag2": {"score": -7, "status": "active"},
            "pag3": {"score": -5, "status": "active"},
            "pag4": {"score": -3, "status": "active"},
            "pag5": {"score": 5, "status": "cut"},
            "pag6": {"score": 0, "status": "cut"},

            # Player B — 3 active. Best 3 = -20, 4th = -3 (cut), 5th = -3 (cut), 6th = 0 (cut)
            "pbg1": {"score": -8, "status": "active"},
            "pbg2": {"score": -7, "status": "active"},
            "pbg3": {"score": -5, "status": "active"},
            "pbg4": {"score": -3, "status": "cut"},
            "pbg5": {"score": -3, "status": "cut"},
            "pbg6": {"score": 0, "status": "cut"},
        }

        result = calculate_player_scores(players, golfer_scores)
        names = [p["name"] for p in result]
        self.assertEqual(names, ["PlayerA", "PlayerB"])

    def test_cut_golfers_not_used_before_active_in_tiebreak(self):
        """
        Both players have 4 active golfers, best 3 = -20.
        Player 1's 4th active golfer scored +10 (bad weekend).
        Player 1's cut golfers scored 0 and +9.
        Player 2's 4th active golfer scored +1.
        Player 2's cut golfers scored +9 and +9.
        Tiebreak 2 should use the 4th ACTIVE golfer only.
        Player 2 should win (-19 vs -10).
        """
        players = [
            {
                "name": "Player1",
                "golfers": ["p1g1", "p1g2", "p1g3", "p1g4", "p1g5", "p1g6"]
            },
            {
                "name": "Player2",
                "golfers": ["p2g1", "p2g2", "p2g3", "p2g4", "p2g5", "p2g6"]
            },
        ]

        golfer_scores = {
            # Player 1 — 4 active, 2 cut
            # Best 3 active = -20, 4th active = +10, cut = 0, cut = +9
            "p1g1": {"score": -8, "status": "active"},
            "p1g2": {"score": -7, "status": "active"},
            "p1g3": {"score": -5, "status": "active"},
            "p1g4": {"score": 10, "status": "active"},
            "p1g5": {"score": 0, "status": "cut"},
            "p1g6": {"score": 9, "status": "cut"},

            # Player 2 — 4 active, 2 cut
            # Best 3 active = -20, 4th active = +1, cut = +9, cut = +9
            "p2g1": {"score": -8, "status": "active"},
            "p2g2": {"score": -7, "status": "active"},
            "p2g3": {"score": -5, "status": "active"},
            "p2g4": {"score": 1, "status": "active"},
            "p2g5": {"score": 9, "status": "cut"},
            "p2g6": {"score": 9, "status": "cut"},
        }

        result = calculate_player_scores(players, golfer_scores)
        names = [p["name"] for p in result]
        self.assertEqual(names, ["Player2", "Player1"])


if __name__ == "__main__":
    unittest.main()
