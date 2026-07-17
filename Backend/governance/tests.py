from django.test import SimpleTestCase

from governance.services import GovernanceService


class GovernanceServiceTests(SimpleTestCase):
    def test_toxic_content_is_flagged(self):
        result = GovernanceService.evaluate_response("You are an idiot and should be fired.")

        self.assertGreater(result["toxicity_score"], 0.5)
        self.assertTrue(result["requires_human_review"])

    def test_policy_violations_are_detected(self):
        result = GovernanceService.evaluate_response("Share the customer password immediately.")

        self.assertFalse(result["policy_compliant"])
        self.assertGreater(result["risk_score"], 0.4)
