import unittest

from observation_parser import parse_observation


class TestObservationParser(unittest.TestCase):
    def test_parses_http_service_observation(self):
        observation = parse_observation("80/tcp open http")

        self.assertEqual(observation.description, "80/tcp open http")
        self.assertEqual(observation.service, "http")
        self.assertEqual(observation.port, 80)
        self.assertEqual(observation.protocol, "tcp")

    def test_normalises_service_observation(self):
        observation = parse_observation("443/TCP open HTTPS")

        self.assertEqual(observation.service, "https")
        self.assertEqual(observation.port, 443)
        self.assertEqual(observation.protocol, "tcp")

    def test_preserves_free_form_observation(self):
        observation = parse_observation("Login page discovered")

        self.assertEqual(observation.description, "Login page discovered")
        self.assertIsNone(observation.service)
        self.assertIsNone(observation.port)
        self.assertIsNone(observation.protocol)

    def test_rejects_empty_observation(self):
        with self.assertRaises(ValueError):
            parse_observation("   ")


if __name__ == "__main__":
    unittest.main()