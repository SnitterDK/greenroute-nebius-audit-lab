import io
import json
import unittest

from nebius_audit import audit_decision


class AuditTests(unittest.TestCase):
    decision = {"estimate": {"centre_wh": 18.4, "min_wh": 13.8, "max_wh": 24.2}}

    @staticmethod
    def fake(request, timeout=0):
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": "Review required"}}], "usage": {"total_tokens": 30}}).encode())

    def test_offline_evidence(self):
        result = audit_decision(self.decision, "nvidia/test-fixture", "test-secret", transport=self.fake)
        self.assertEqual(result["usage"], {"total_tokens": 30})
        self.assertFalse(result["route_changed"])
        self.assertFalse(result["user_prompt_transmitted"])
        self.assertNotIn("test-secret", json.dumps(result))

    def test_live_disabled(self):
        with self.assertRaisesRegex(ValueError, "Live requests disabled"):
            audit_decision(self.decision, "nvidia/test-fixture", "test-secret")

    def test_other_model_rejected(self):
        with self.assertRaisesRegex(ValueError, "NVIDIA"):
            audit_decision(self.decision, "other/model", "test-secret", transport=self.fake)

    def test_no_numeric_evidence(self):
        with self.assertRaisesRegex(ValueError, "No numerical"):
            audit_decision({}, "nvidia/test-fixture", "test-secret", transport=self.fake)

    def test_errors_redacted(self):
        def broken(*args, **kwargs):
            raise RuntimeError("test-secret")
        with self.assertRaisesRegex(RuntimeError, "no route was changed") as ctx:
            audit_decision(self.decision, "nvidia/test-fixture", "test-secret", transport=broken)
        self.assertNotIn("test-secret", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
