import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_site_quality import validate  # noqa: E402


class SiteQualityTests(unittest.TestCase):
    def test_site_quality_has_no_errors(self):
        self.assertEqual(validate(), [])


if __name__ == "__main__":
    unittest.main()
