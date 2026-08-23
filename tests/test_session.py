import unittest

from session import SentinelSession, SessionStatus
from state import Observation


class SentinelSessionTests(unittest.TestCase):
    def setUp(self):
        self.session = SentinelSession()

    def test_session_starts_with_empty_operator_context(self):
        status = self.session.status()

        self.assertEqual(
            status,
            SessionStatus(
                target="",
                objective="",
                phase="enumeration",
                observations=(),
                findings=(),
                actions_completed=(),
                evidence=(),
            ),
        )

    def test_sets_target(self):
        self.session.set_target("10.10.10.10")

        self.assertEqual(
            self.session.status().target,
            "10.10.10.10",
        )

    def test_rejects_empty_target(self):
        with self.assertRaises(ValueError):
            self.session.set_target("   ")

    def test_sets_objective(self):
        self.session.set_objective(
            "Linux privilege escalation"
        )

        self.assertEqual(
            self.session.status().objective,
            "Linux privilege escalation",
        )

    def test_rejects_empty_objective(self):
        with self.assertRaises(ValueError):
            self.session.set_objective("   ")

    def test_sets_phase(self):
        self.session.set_phase(
            "privilege escalation"
        )

        self.assertEqual(
            self.session.status().phase,
            "privilege escalation",
        )

    def test_rejects_empty_phase(self):
        with self.assertRaises(ValueError):
            self.session.set_phase("   ")

    def test_records_structured_observation(self):
        observation = self.session.record_observation(
            "80/tcp open http"
        )

        self.assertEqual(
            observation,
            Observation(
                description="80/tcp open http",
                service="http",
                port=80,
                protocol="tcp",
            ),
        )

        self.assertEqual(
            self.session.status().observations,
            (
                Observation(
                    description="80/tcp open http",
                    service="http",
                    port=80,
                    protocol="tcp",
                ),
            ),
        )

    def test_preserves_free_form_observation(self):
        observation = self.session.record_observation(
            "The application appears to use a custom login page."
        )

        self.assertEqual(
            observation,
            Observation(
                description=(
                    "The application appears to use "
                    "a custom login page."
                )
            ),
        )

    def test_status_returns_snapshot_of_engagement_state(self):
        self.session.set_target("10.10.10.10")
        self.session.set_objective(
            "Web enumeration"
        )
        self.session.set_phase("enumeration")

        self.session.record_observation(
            "80/tcp open http"
        )

        self.session.engagement.findings.append(
            "Custom login page"
        )
        self.session.engagement.actions_completed.append(
            "enumerate_http"
        )
        self.session.engagement.evidence.append(
            "login-page.png"
        )

        status = self.session.status()

        self.assertEqual(
            status.target,
            "10.10.10.10",
        )
        self.assertEqual(
            status.objective,
            "Web enumeration",
        )
        self.assertEqual(
            status.phase,
            "enumeration",
        )
        self.assertEqual(
            status.findings,
            ("Custom login page",),
        )
        self.assertEqual(
            status.actions_completed,
            ("enumerate_http",),
        )
        self.assertEqual(
            status.evidence,
            ("login-page.png",),
        )

    def test_status_snapshot_does_not_expose_mutable_state_lists(self):
        self.session.record_observation(
            "80/tcp open http"
        )

        status = self.session.status()

        self.assertIsInstance(
            status.observations,
            tuple,
        )
        self.assertIsInstance(
            status.findings,
            tuple,
        )
        self.assertIsInstance(
            status.actions_completed,
            tuple,
        )
        self.assertIsInstance(
            status.evidence,
            tuple,
        )


if __name__ == "__main__":
    unittest.main()