import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import generate_cv_bibliometrics as updater


class MetricsTests(unittest.TestCase):
    def test_scopus_response(self):
        with patch.dict("os.environ", {"ELSEVIER_API_KEY": "test"}):
            with patch.object(updater.requests, "get") as get:
                get.return_value.json.return_value = {
                    "author-retrieval-response": [{
                        "coredata": {"dc:identifier": "AUTHOR_ID:57188983512",
                                     "citation-count": "340", "document-count": "34"},
                        "h-index": "12"
                    }]
                }
                self.assertEqual(updater.scopus(), {"Citations": 340, "Documents": 34, "h-index": 12})
                self.assertEqual(get.call_args.kwargs["params"], {"view": "METRICS"})

    def test_scholar_period(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scholar.json"
            path.write_text(json.dumps({
                "scholar_id": "RvAqXUIAAAAJ", "recent_period": "Since 2022",
                "citations": 707, "citations_recent": 601,
                "h_index": 16, "h_index_recent": 15,
                "i10_index": 25, "i10_index_recent": 21
            }))
            self.assertEqual(updater.scholar(path)["Citations"], "707--601 (All--since 2022)")

    def test_preserve_other_sections(self):
        original = r"\subsection*{Scopus}" + "\n" + r"\item \textbf{Citations}: 340" + "\n"
        suffix = r"\subsection*{Web of Science}" + "\n" + r"\item \textbf{Citations}: 251"
        result = updater.replace_section(original + suffix, "Scopus", {"Citations": 350})
        self.assertEqual(result, original.replace("340", "350") + suffix)
        with self.assertRaises(ValueError):
            updater.replace_section(original, "Scopus", {"Documents": 34})

    def test_bad_metric(self):
        for value in (None, -1, True, "unknown"):
            with self.assertRaises(ValueError):
                updater.integer(value)


if __name__ == "__main__":
    unittest.main()
