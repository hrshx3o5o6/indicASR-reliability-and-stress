import json
import tempfile
import unittest
from pathlib import Path

from run_baseline import load_manifest, json_safe_lid, write_record


class BaselineRunnerTests(unittest.TestCase):
    def test_load_manifest_skips_blank_lines_and_preserves_annotations(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.jsonl"
            manifest.write_text(
                '\n'
                '{"id":"ta-001","audio":"a.wav","language":"ta",'
                '"reference":"வணக்கம்","condition":["clean"]}\n',
                encoding="utf-8",
            )

            samples = load_manifest(manifest)

        self.assertEqual(samples[0]["id"], "ta-001")
        self.assertEqual(samples[0]["condition"], ["clean"])

    def test_load_manifest_rejects_missing_required_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.jsonl"
            manifest.write_text('{"id":"bad","audio":"a.wav"}\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "language"):
                load_manifest(manifest)

    def test_load_manifest_accepts_canonical_nested_annotation_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.jsonl"
            manifest.write_text(
                '{"sample_id":"cs-v0-ta-001","audio":{"path":"ta.wav"},'
                '"language":"ta","conditions":{"audio":["clean"],'
                '"content":["normal"]},"provenance":{"source":"fleurs"}}\n',
                encoding="utf-8",
            )

            samples = load_manifest(manifest)

        self.assertEqual(samples[0]["id"], "cs-v0-ta-001")
        self.assertEqual(samples[0]["audio_path"], "ta.wav")
        self.assertEqual(samples[0]["condition"], ["clean", "normal"])
        self.assertEqual(samples[0]["provenance"]["source"], "fleurs")

    def test_json_safe_lid_converts_tuples_to_json_arrays(self):
        value = json_safe_lid([("ta", 0.75), ("hi", 0.25)])

        self.assertEqual(value, [["ta", 0.75], ["hi", 0.25]])
        json.dumps(value)

    def test_write_record_writes_unicode_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "results.jsonl"
            write_record(output, {"id": "ta-001", "transcript": "வணக்கம்"})

            content = output.read_text(encoding="utf-8")

        self.assertEqual(json.loads(content)["transcript"], "வணக்கம்")


if __name__ == "__main__":
    unittest.main()
