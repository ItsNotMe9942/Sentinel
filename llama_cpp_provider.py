import json
from urllib import error, request

from model_gateway import ModelRequest, ModelResponse


class LlamaCppProvider:
    def __init__(
        self,
        model: str = "ggml-org/Qwen3-1.7B-GGUF:Q4_K_M",
        base_url: str = "http://127.0.0.1:8080",
        timeout: int = 120,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(
        self,
        model_request: ModelRequest,
    ) -> ModelResponse:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": model_request.prompt,
                }
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        encoded_payload = json.dumps(
            payload
        ).encode("utf-8")

        http_request = request.Request(
            (
                f"{self.base_url}"
                "/v1/chat/completions"
            ),
            data=encoded_payload,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(
                http_request,
                timeout=self.timeout,
            ) as response:
                response_body = response.read()

        except error.HTTPError as exc:
            raise ConnectionError(
                "Local reasoning provider returned "
                f"HTTP {exc.code}."
            ) from exc

        except error.URLError as exc:
            raise ConnectionError(
                "Unable to reach the local reasoning provider."
            ) from exc

        try:
            data = json.loads(
                response_body.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ValueError(
                "Local reasoning provider returned "
                "an invalid response."
            ) from exc

        try:
            content = (
                data["choices"][0]["message"]["content"]
            )
        except (
            KeyError,
            IndexError,
            TypeError,
        ) as exc:
            raise ValueError(
                "Local reasoning provider returned "
                "an unexpected response structure."
            ) from exc

        if not isinstance(content, str):
            raise ValueError(
                "Local reasoning provider returned "
                "non-text content."
            )

        return ModelResponse(
            content=content.strip()
        )