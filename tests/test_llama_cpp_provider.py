import json
import unittest
from unittest.mock import patch
from urllib import error

from llama_cpp_provider import LlamaCppProvider
from model_gateway import ModelRequest, ModelResponse


class FakeHTTPResponse:
    def __init__(self, data: dict) -> None:
        self.body = json.dumps(data).encode(
            "utf-8"
        )

    def read(self) -> bytes:
        return self.body

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        return None


class LlamaCppProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = LlamaCppProvider(
            model="test-model",
            base_url="http://127.0.0.1:8080",
            timeout=30,
            temperature=0.2,
            max_tokens=256,
        )

    @patch(
        "llama_cpp_provider.request.urlopen"
    )
    def test_sends_request_to_chat_completion_endpoint(
        self,
        mock_urlopen,
    ):
        mock_urlopen.return_value = (
            FakeHTTPResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": "Test response"
                            }
                        }
                    ]
                }
            )
        )

        self.provider.generate(
            ModelRequest(
                prompt="Explain this observation."
            )
        )

        http_request = (
            mock_urlopen.call_args.args[0]
        )

        self.assertEqual(
            http_request.full_url,
            (
                "http://127.0.0.1:8080"
                "/v1/chat/completions"
            ),
        )

    @patch(
        "llama_cpp_provider.request.urlopen"
    )
    def test_sends_model_request_as_user_message(
        self,
        mock_urlopen,
    ):
        mock_urlopen.return_value = (
            FakeHTTPResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": "Test response"
                            }
                        }
                    ]
                }
            )
        )

        self.provider.generate(
            ModelRequest(
                prompt="Explain this observation."
            )
        )

        http_request = (
            mock_urlopen.call_args.args[0]
        )

        payload = json.loads(
            http_request.data.decode("utf-8")
        )

        self.assertEqual(
            payload["model"],
            "test-model",
        )

        self.assertEqual(
            payload["messages"],
            [
                {
                    "role": "user",
                    "content": (
                        "Explain this observation."
                    ),
                }
            ],
        )

        self.assertFalse(
            payload["stream"]
        )

    @patch(
        "llama_cpp_provider.request.urlopen"
    )
    def test_returns_model_response(
        self,
        mock_urlopen,
    ):
        mock_urlopen.return_value = (
            FakeHTTPResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    "Review the HTTP service."
                                )
                            }
                        }
                    ]
                }
            )
        )

        response = self.provider.generate(
            ModelRequest(
                prompt="What should I review?"
            )
        )

        self.assertEqual(
            response,
            ModelResponse(
                content=(
                    "Review the HTTP service."
                )
            ),
        )

    @patch(
        "llama_cpp_provider.request.urlopen"
    )
    def test_strips_response_whitespace(
        self,
        mock_urlopen,
    ):
        mock_urlopen.return_value = (
            FakeHTTPResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    "  Useful response.  "
                                )
                            }
                        }
                    ]
                }
            )
        )

        response = self.provider.generate(
            ModelRequest(
                prompt="Question"
            )
        )

        self.assertEqual(
            response.content,
            "Useful response.",
        )

    @patch(
        "llama_cpp_provider.request.urlopen"
    )
    def test_connection_failure_raises_connection_error(
        self,
        mock_urlopen,
    ):
        mock_urlopen.side_effect = (
            error.URLError(
                "Connection refused"
            )
        )

        with self.assertRaises(
            ConnectionError
        ):
            self.provider.generate(
                ModelRequest(
                    prompt="Question"
                )
            )

    @patch(
        "llama_cpp_provider.request.urlopen"
    )
    def test_http_failure_raises_connection_error(
        self,
        mock_urlopen,
    ):
        mock_urlopen.side_effect = (
            error.HTTPError(
                url=(
                    "http://127.0.0.1:8080"
                    "/v1/chat/completions"
                ),
                code=500,
                msg="Server error",
                hdrs=None,
                fp=None,
            )
        )

        with self.assertRaises(
            ConnectionError
        ):
            self.provider.generate(
                ModelRequest(
                    prompt="Question"
                )
            )

    @patch(
        "llama_cpp_provider.request.urlopen"
    )
    def test_invalid_json_response_is_rejected(
        self,
        mock_urlopen,
    ):
        class InvalidResponse:
            def read(self) -> bytes:
                return b"not-json"

            def __enter__(self):
                return self

            def __exit__(
                self,
                exc_type,
                exc_value,
                traceback,
            ) -> None:
                return None

        mock_urlopen.return_value = (
            InvalidResponse()
        )

        with self.assertRaises(
            ValueError
        ):
            self.provider.generate(
                ModelRequest(
                    prompt="Question"
                )
            )

    @patch(
        "llama_cpp_provider.request.urlopen"
    )
    def test_unexpected_response_structure_is_rejected(
        self,
        mock_urlopen,
    ):
        mock_urlopen.return_value = (
            FakeHTTPResponse(
                {
                    "unexpected": "response"
                }
            )
        )

        with self.assertRaises(
            ValueError
        ):
            self.provider.generate(
                ModelRequest(
                    prompt="Question"
                )
            )


if __name__ == "__main__":
    unittest.main()