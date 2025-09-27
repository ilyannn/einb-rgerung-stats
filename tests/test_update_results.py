import datetime as dt
import tempfile
from pathlib import Path
from unittest import TestCase, mock

import update_results

SAMPLE_SENTENCE = "Derzeit werden Anträge mit Eingangsdatum bis Ende April 2023 bearbeitet (Stand: 28.08.2025)."
SAMPLE_HTML = f"<html><body><p>{SAMPLE_SENTENCE}</p></body></html>"


class UpdateResultsTests(TestCase):
    def test_extract_status_sentence(self) -> None:
        sentence = update_results.extract_status_sentence(SAMPLE_HTML)
        self.assertEqual(sentence, SAMPLE_SENTENCE)

    def test_parse_target_date_end_of_month(self) -> None:
        target_date = update_results.parse_target_date(SAMPLE_SENTENCE)
        self.assertEqual(target_date, dt.date(2023, 4, 30))

    def test_append_row_if_changed(self) -> None:
        row = [
            "2025-02-22",
            "2025-08-28",
            SAMPLE_SENTENCE,
            "2023-04-30",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "results.csv"
            wrote = update_results.append_row_if_changed(csv_path, row)
            self.assertTrue(wrote)
            wrote_again = update_results.append_row_if_changed(csv_path, row)
            self.assertFalse(wrote_again)
            contents = csv_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(contents), 2)

    @mock.patch("update_results.urlopen")
    def test_main_appends_new_row(self, mock_urlopen: mock.MagicMock) -> None:
        response = mock.MagicMock()
        response.read.return_value = SAMPLE_HTML.encode("utf-8")
        response.headers.get_content_charset.return_value = "utf-8"
        mock_urlopen.return_value.__enter__.return_value = response

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "results.csv"
            exit_code = update_results.main(["--csv", str(csv_path)])
            self.assertEqual(exit_code, 0)
            data = csv_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(data), 2)
            self.assertIn("2023-04-30", data[1])
            today = dt.date.today().isoformat()
            self.assertTrue(data[1].startswith(today))

            exit_code_second = update_results.main(["--csv", str(csv_path)])
            self.assertEqual(exit_code_second, 0)
            data_second = csv_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(data_second), 2)
