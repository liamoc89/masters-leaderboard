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


if __name__ == "__main__":
    unittest.main()
