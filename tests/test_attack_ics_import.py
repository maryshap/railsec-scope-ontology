"""Fast, dependency-free guards for the controlled ATT&CK ICS projection."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("import_attack_ics", PROJECT / "scripts" / "import_attack_ics.py")
IMPORTER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(IMPORTER)


class AttackICSImportTest(unittest.TestCase):
    def _files(self, directory: Path) -> tuple[Path, Path]:
        objects = [
            {"type": "x-mitre-collection", "id": "collection", "x_mitre_version": "test"},
            {"type": "x-mitre-tactic", "id": "tactic", "name": "Initial Access", "x_mitre_shortname": "initial-access", "external_references": [{"source_name": "mitre-attack", "external_id": "TA0001", "url": "https://example.test/tactic"}]},
            {"type": "attack-pattern", "id": "active", "name": "Active technique", "kill_chain_phases": [{"kill_chain_name": "mitre-ics-attack", "phase_name": "initial-access"}], "external_references": [{"source_name": "mitre-attack", "external_id": "T0001", "url": "https://example.test/active"}]},
            {"type": "attack-pattern", "id": "revoked", "name": "Revoked technique", "revoked": True, "kill_chain_phases": [{"kill_chain_name": "mitre-ics-attack", "phase_name": "initial-access"}], "external_references": [{"source_name": "mitre-attack", "external_id": "T0002", "url": "https://example.test/revoked"}]},
        ]
        source = directory / "source.json"
        source.write_text(json.dumps({"type": "bundle", "objects": objects}), encoding="utf-8")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        manifest = directory / "manifest.json"
        manifest.write_text(json.dumps({
            "source_sha256": digest,
            "collection_id": "collection",
            "collection_version": "test",
            "include_object_types": ["x-mitre-tactic", "attack-pattern"],
            "exclude_revoked": True,
            "exclude_deprecated": True,
            "expected_active_tactics": 1,
            "expected_active_techniques": 1,
            "projection_policy": "test projection",
        }), encoding="utf-8")
        return source, manifest

    def test_projection_is_deterministic_and_excludes_revoked_objects(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source, manifest = self._files(Path(temp))
            first = IMPORTER.project(source, manifest)
            second = IMPORTER.project(source, manifest)
        self.assertEqual(first, second)
        self.assertIn("T0001", first)
        self.assertNotIn("T0002", first)
        self.assertIn("techniqueInTactic", first)

    def test_source_digest_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source, manifest = self._files(Path(temp))
            source.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                IMPORTER.project(source, manifest)

    def test_committed_projection_matches_its_manifest(self) -> None:
        manifest = json.loads(
            (PROJECT / "imports" / "attack-ics-19.2-projection.json").read_text(encoding="utf-8")
        )
        projection = (PROJECT / "imports" / "attack-ics-19.2.ttl").read_bytes()
        self.assertEqual(manifest["projection_sha256"], hashlib.sha256(projection).hexdigest())
        text = projection.decode("utf-8")
        self.assertEqual(manifest["expected_active_tactics"], text.count("a rss-attack:AttackTactic"))
        self.assertEqual(manifest["expected_active_techniques"], text.count("a rss-attack:AttackTechnique"))


if __name__ == "__main__":
    unittest.main()
