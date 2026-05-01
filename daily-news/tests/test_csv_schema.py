"""
Unittest for daily-news CSV schema validation.

Checks performed:
  1. All events.csv files under daily-news/data/ contain the required columns.
  2. All event_tags.csv files under daily-news/data/ contain the required columns.
  3. Every event_type value in events.csv is a valid taxonomy value defined in
     daily-news/data/taxonomy/taxonomy_values.csv (dimension == "event_type").
  4. Every dimension value in event_tags.csv exists in taxonomy_dimensions.csv.
  5. Every normalized_value in event_tags.csv is a valid value for its dimension
     in taxonomy_values.csv — but only for dimensions whose value_mode is "closed".
     Dimensions with value_mode "dynamic" allow any stable lowercase snake_case slug.
"""

import csv
import pathlib
import re
import unittest

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "daily-news" / "data"
TAXONOMY_CSV = DATA_DIR / "taxonomy" / "taxonomy_values.csv"
TAXONOMY_DIMENSIONS_CSV = DATA_DIR / "taxonomy" / "taxonomy_dimensions.csv"

# ---------------------------------------------------------------------------
# Expected columns
# ---------------------------------------------------------------------------
EVENTS_REQUIRED_COLUMNS = {
    "event_key",
    "date",
    "week",
    "month",
    "event_type",
    "title",
    "summary",
    "source_file",
    "source_url",
    "confidence",
    "needs_review",
    "monthly_followup_candidate",
}

EVENT_TAGS_REQUIRED_COLUMNS = {
    "event_key",
    "dimension",
    "raw_value",
    "normalized_value",
    "confidence",
    "note",
}


# ---------------------------------------------------------------------------
# Taxonomy loaders
# ---------------------------------------------------------------------------
def load_taxonomy(taxonomy_csv: pathlib.Path) -> dict[str, set[str]]:
    """Return {dimension: {normalized_value, ...}} from taxonomy_values.csv."""
    taxonomy: dict[str, set[str]] = {}
    with taxonomy_csv.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            dim = row["dimension"].strip()
            val = row["normalized_value"].strip()
            if dim:
                taxonomy.setdefault(dim, set()).add(val)
    return taxonomy


def load_dimension_modes(dimensions_csv: pathlib.Path) -> dict[str, str]:
    """Return {dimension: value_mode} from taxonomy_dimensions.csv.

    value_mode is either "closed" (normalized_value must exist in taxonomy_values)
    or "dynamic" (any stable lowercase snake_case slug is acceptable).
    """
    modes: dict[str, str] = {}
    with dimensions_csv.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            dim = row["dimension"].strip()
            mode = row["value_mode"].strip()
            if dim:
                modes[dim] = mode
    return modes


_SNAKE_CASE_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


# ---------------------------------------------------------------------------
# File discovery helpers
# ---------------------------------------------------------------------------
def find_events_csvs() -> list[pathlib.Path]:
    return sorted(DATA_DIR.rglob("events.csv"))


def find_event_tags_csvs() -> list[pathlib.Path]:
    return sorted(DATA_DIR.rglob("event_tags.csv"))


def read_csv_rows(path: pathlib.Path) -> tuple[list[str], list[dict]]:
    """Return (header_columns, list_of_row_dicts)."""
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = list(reader.fieldnames or [])
    return columns, rows


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestEventsCSVSchema(unittest.TestCase):
    """Schema validation tests for events.csv files."""

    @classmethod
    def setUpClass(cls):
        cls.taxonomy = load_taxonomy(TAXONOMY_CSV)
        cls.valid_event_types: set[str] = cls.taxonomy.get("event_type", set())
        cls.csv_files = find_events_csvs()

    def test_at_least_one_events_csv_exists(self):
        self.assertGreater(
            len(self.csv_files),
            0,
            f"No events.csv found under {DATA_DIR}",
        )

    def test_required_columns_present(self):
        for csv_path in self.csv_files:
            with self.subTest(file=str(csv_path.relative_to(REPO_ROOT))):
                columns, _ = read_csv_rows(csv_path)
                actual = set(columns)
                missing = EVENTS_REQUIRED_COLUMNS - actual
                self.assertFalse(
                    missing,
                    f"{csv_path.relative_to(REPO_ROOT)}: missing columns: {missing}",
                )

    def test_no_empty_event_key(self):
        for csv_path in self.csv_files:
            with self.subTest(file=str(csv_path.relative_to(REPO_ROOT))):
                _, rows = read_csv_rows(csv_path)
                for i, row in enumerate(rows, start=2):
                    self.assertTrue(
                        row.get("event_key", "").strip(),
                        f"{csv_path.relative_to(REPO_ROOT)} row {i}: event_key is empty",
                    )

    def test_event_type_is_valid_taxonomy_value(self):
        self.assertTrue(
            self.valid_event_types,
            "No event_type values loaded from taxonomy — check taxonomy_values.csv",
        )
        for csv_path in self.csv_files:
            with self.subTest(file=str(csv_path.relative_to(REPO_ROOT))):
                _, rows = read_csv_rows(csv_path)
                for i, row in enumerate(rows, start=2):
                    et = row.get("event_type", "").strip()
                    self.assertIn(
                        et,
                        self.valid_event_types,
                        f"{csv_path.relative_to(REPO_ROOT)} row {i}: "
                        f"event_type '{et}' is not in taxonomy. "
                        f"Valid values: {sorted(self.valid_event_types)}",
                    )


class TestEventTagsCSVSchema(unittest.TestCase):
    """Schema validation tests for event_tags.csv files."""

    @classmethod
    def setUpClass(cls):
        cls.taxonomy = load_taxonomy(TAXONOMY_CSV)
        cls.dimension_modes = load_dimension_modes(TAXONOMY_DIMENSIONS_CSV)
        cls.csv_files = find_event_tags_csvs()

    def test_at_least_one_event_tags_csv_exists(self):
        self.assertGreater(
            len(self.csv_files),
            0,
            f"No event_tags.csv found under {DATA_DIR}",
        )

    def test_required_columns_present(self):
        for csv_path in self.csv_files:
            with self.subTest(file=str(csv_path.relative_to(REPO_ROOT))):
                columns, _ = read_csv_rows(csv_path)
                actual = set(columns)
                missing = EVENT_TAGS_REQUIRED_COLUMNS - actual
                self.assertFalse(
                    missing,
                    f"{csv_path.relative_to(REPO_ROOT)}: missing columns: {missing}",
                )

    def test_no_empty_event_key(self):
        for csv_path in self.csv_files:
            with self.subTest(file=str(csv_path.relative_to(REPO_ROOT))):
                _, rows = read_csv_rows(csv_path)
                for i, row in enumerate(rows, start=2):
                    self.assertTrue(
                        row.get("event_key", "").strip(),
                        f"{csv_path.relative_to(REPO_ROOT)} row {i}: event_key is empty",
                    )

    def test_dimension_exists_in_taxonomy(self):
        for csv_path in self.csv_files:
            with self.subTest(file=str(csv_path.relative_to(REPO_ROOT))):
                _, rows = read_csv_rows(csv_path)
                for i, row in enumerate(rows, start=2):
                    dim = row.get("dimension", "").strip()
                    self.assertIn(
                        dim,
                        self.dimension_modes,
                        f"{csv_path.relative_to(REPO_ROOT)} row {i}: "
                        f"dimension '{dim}' is not in taxonomy_dimensions.csv. "
                        f"Valid dimensions: {sorted(self.dimension_modes.keys())}",
                    )

    def test_normalized_value_is_valid_for_closed_dimension(self):
        """For closed-vocabulary dimensions, normalized_value must exist in taxonomy_values.csv.

        Dynamic dimensions (value_mode == "dynamic") allow any stable lowercase
        snake_case slug and are skipped by this check.
        """
        for csv_path in self.csv_files:
            with self.subTest(file=str(csv_path.relative_to(REPO_ROOT))):
                _, rows = read_csv_rows(csv_path)
                for i, row in enumerate(rows, start=2):
                    dim = row.get("dimension", "").strip()
                    val = row.get("normalized_value", "").strip()
                    mode = self.dimension_modes.get(dim)
                    if mode != "closed":
                        # dynamic dimension: only verify lowercase snake_case format
                        self.assertTrue(
                            _SNAKE_CASE_RE.match(val),
                            f"{csv_path.relative_to(REPO_ROOT)} row {i}: "
                            f"normalized_value '{val}' for dynamic dimension '{dim}' "
                            f"must be lowercase snake_case",
                        )
                        continue
                    if dim not in self.taxonomy:
                        continue  # already caught by test_dimension_exists_in_taxonomy
                    self.assertIn(
                        val,
                        self.taxonomy[dim],
                        f"{csv_path.relative_to(REPO_ROOT)} row {i}: "
                        f"normalized_value '{val}' is not valid for closed dimension '{dim}'. "
                        f"Valid values: {sorted(self.taxonomy[dim])}",
                    )


if __name__ == "__main__":
    unittest.main()
