import unittest

from model_gateway import ModelGateway, ModelRequest, ModelResponse


class FakeProvider:
    def __init__(self, response_content: str = "Test response") -> None:
        self.response_content = response_content
        self.last_request: ModelRequest | None = None

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.last_request = request

        return ModelResponse(content=self.response_content)


class ModelGatewayTests(unittest.TestCase):
    def test_gateway_sends_structured_request_to_provider(self):
        provider = FakeProvider()
        gateway = ModelGateway(provider)

        gateway.request("Review the current engagement state.")

        self.assertIsNotNone(provider.last_request)
        self.assertEqual(
            provider.last_request.prompt,
            "Review the current engagement state.",
        )

    def test_gateway_returns_provider_response(self):
        provider = FakeProvider(
            response_content="Review the HTTP observations."
        )
        gateway = ModelGateway(provider)

        response = gateway.request("What should Sentinel consider next?")

        self.assertEqual(
            response,
            ModelResponse(content="Review the HTTP observations."),
        )

    def test_gateway_rejects_empty_prompt(self):
        provider = FakeProvider()
        gateway = ModelGateway(provider)

        with self.assertRaises(ValueError):
            gateway.request("   ")

        self.assertIsNone(provider.last_request)


if __name__ == "__main__":
    unittest.main()