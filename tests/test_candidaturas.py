import csv
import tempfile
import unittest
from pathlib import Path

from candidaturas import Tracker, main


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / "test.db"
        self.tracker = Tracker(self.database)

    def test_add_persists_between_connections(self):
        identifier = self.tracker.add("Empresa Exemplo", "Estágio Python", "2026-11-02")
        self.assertEqual(Tracker(self.database).list()[0]["id"], identifier)
        self.assertEqual(self.tracker.list()[0]["status"], "enviada")

    def test_rejects_empty_fields_and_invalid_dates(self):
        for company, role, day in [(" ", "dev", None), ("A", " ", None), ("A", "dev", "2026-02-30")]:
            with self.subTest(company=company, role=role, day=day), self.assertRaises(ValueError):
                self.tracker.add(company, role, day)
        self.assertEqual(self.tracker.list(), [])

    def test_update_filter_and_summary(self):
        first = self.tracker.add("A", "Python")
        self.tracker.add("B", "Backend")
        self.tracker.update(first, "entrevista")
        self.assertEqual(len(self.tracker.list("entrevista")), 1)
        self.assertEqual(self.tracker.summary(), {"enviada": 1, "entrevista": 1, "oferta": 0, "encerrada": 0})

    def test_missing_id_and_invalid_status(self):
        with self.assertRaises(ValueError):
            self.tracker.update(999, "oferta")
        with self.assertRaises(ValueError):
            self.tracker.update(1, "qualquer")
        with self.assertRaises(ValueError):
            self.tracker.list("qualquer")

    def test_sql_is_treated_as_data(self):
        company = "Exemplo'); DROP TABLE applications; --"
        self.tracker.add(company, "Python")
        self.assertEqual(self.tracker.list()[0]["company"], company)
        self.tracker.add("Outra", "Python")
        self.assertEqual(len(self.tracker.list()), 2)

    def test_export_escapes_formulas_and_preserves_unicode(self):
        self.tracker.add("=1+1", "Estágio, Python")
        target = Path(self.directory.name) / "saida.csv"
        self.assertEqual(self.tracker.export(target), 1)
        with target.open(encoding="utf-8", newline="") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual(row["company"], "'=1+1")
        self.assertEqual(row["role"], "Estágio, Python")

    def test_cli_returns_error_for_missing_application(self):
        self.assertEqual(main(["--db", str(self.database), "atualizar", "99", "oferta"]), 1)

    def test_export_cannot_overwrite_database(self):
        self.tracker.add("Empresa", "Python")
        with self.assertRaises(ValueError):
            self.tracker.export(self.database)
        self.assertEqual(len(self.tracker.list()), 1)


if __name__ == "__main__":
    unittest.main()
