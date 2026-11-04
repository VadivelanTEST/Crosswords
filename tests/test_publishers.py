import unittest
from unittest.mock import Mock, patch

import start
import start_mini


def puzzle_payload(date="11/04/2026"):
    return {
        "date": date,
        "clues": {"across": ["Clue A"], "down": ["Clue D"]},
        "answers": {"across": ["ANSWER"], "down": ["WORD"]},
    }


def mini_payload(date="11/04/2026"):
    payload = puzzle_payload(date)
    payload["size"] = {"rows": 5, "cols": 5}
    return payload


class DailyPublisherValidationTests(unittest.TestCase):
    @patch("start.requests.get")
    def test_accepts_complete_matching_puzzle(self, get):
        response = Mock()
        response.json.return_value = puzzle_payload()
        response.raise_for_status.return_value = None
        get.return_value = response

        result = start.fetch_crossword_data("11/04/2026")

        self.assertEqual(result["date"], "11/04/2026")

    @patch("start.requests.get")
    def test_rejects_mismatched_clue_answer_counts(self, get):
        response = Mock()
        payload = puzzle_payload()
        payload["answers"]["across"] = []
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        get.return_value = response

        with self.assertRaisesRegex(ValueError, "counts do not match"):
            start.fetch_crossword_data("11/04/2026")

    @patch("start.requests.get")
    def test_rejects_wrong_puzzle_date(self, get):
        response = Mock()
        response.json.return_value = puzzle_payload("11/03/2026")
        response.raise_for_status.return_value = None
        get.return_value = response

        with self.assertRaisesRegex(ValueError, "date mismatch"):
            start.fetch_crossword_data("11/04/2026")


class MiniPublisherValidationTests(unittest.TestCase):
    @patch("start_mini.requests.get")
    def test_accepts_verified_5x5_mini(self, get):
        response = Mock()
        response.json.return_value = mini_payload()
        response.raise_for_status.return_value = None
        get.return_value = response

        result = start_mini.fetch_mini_data("https://example.test/{date}", "11/04/2026")

        self.assertEqual(result["size"], {"rows": 5, "cols": 5})

    @patch("start_mini.requests.get")
    def test_rejects_full_size_or_unknown_grid(self, get):
        response = Mock()
        payload = mini_payload()
        payload["size"] = {"rows": 15, "cols": 15}
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        get.return_value = response

        with self.assertRaisesRegex(ValueError, "Expected verified 5x5"):
            start_mini.fetch_mini_data("https://example.test/{date}", "11/04/2026")

    @patch("start_mini.requests.get")
    def test_rejects_mismatched_clue_answer_counts(self, get):
        response = Mock()
        payload = mini_payload()
        payload["answers"]["down"] = []
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        get.return_value = response

        with self.assertRaisesRegex(ValueError, "counts do not match"):
            start_mini.fetch_mini_data("https://example.test/{date}", "11/04/2026")


if __name__ == "__main__":
    unittest.main()
