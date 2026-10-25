import unittest

from scripts.train_ml_detector import calculate_event_detection_delays


class TestEventDetectionDelay(unittest.TestCase):

    def make_meta(self, dates, hospital="HOSP_TUN", sim="sim_3001"):
        return [
            {"sim_id": sim, "hospital_id": hospital, "date": day}
            for day in dates
        ]

    def test_immediate_detection(self):
        meta = self.make_meta(["2024-03-01", "2024-03-02"])
        delays, missed = calculate_event_detection_delays(
            meta, [1, 1], [1, 1]
        )
        self.assertEqual(delays, [0])
        self.assertEqual(missed, 0)

    def test_three_day_delay(self):
        meta = self.make_meta([
            "2024-03-01", "2024-03-02",
            "2024-03-03", "2024-03-04"
        ])
        delays, missed = calculate_event_detection_delays(
            meta, [0, 0, 0, 1], [1, 1, 1, 1]
        )
        self.assertEqual(delays, [3])
        self.assertEqual(missed, 0)

    def test_missed_outbreak(self):
        meta = self.make_meta(["2024-03-01", "2024-03-02"])
        delays, missed = calculate_event_detection_delays(
            meta, [0, 0], [1, 1]
        )
        self.assertEqual(delays, [])
        self.assertEqual(missed, 1)

    def test_multiple_hospitals(self):
        dates = ["2024-03-01", "2024-03-02", "2024-03-03"]
        meta = (
            self.make_meta(dates, hospital="HOSP_TUN")
            + self.make_meta(dates, hospital="HOSP_SOU")
        )
        delays, missed = calculate_event_detection_delays(
            meta,
            [0, 1, 1, 0, 0, 0],
            [1, 1, 1, 1, 1, 1]
        )
        self.assertEqual(delays, [1])
        self.assertEqual(missed, 1)

    def test_ignores_healthy_groups(self):
        meta = self.make_meta(["2024-03-01", "2024-03-02"])
        delays, missed = calculate_event_detection_delays(
            meta, [1, 0], [0, 0]
        )
        self.assertEqual(delays, [])
        self.assertEqual(missed, 0)

    def test_ignores_pre_onset_false_alarm(self):
        meta = self.make_meta([
            "2024-03-01", "2024-03-02", "2024-03-03"
        ])
        delays, missed = calculate_event_detection_delays(
            meta, [1, 0, 1], [0, 1, 1]
        )
        self.assertEqual(delays, [1])
        self.assertEqual(missed, 0)


if __name__ == "__main__":
    unittest.main()
