import re

from state import Observation


SERVICE_OBSERVATION_PATTERN = re.compile(
    r"^(?P<port>\d{1,5})/(?P<protocol>tcp|udp)\s+open\s+(?P<service>[a-zA-Z0-9_-]+)$",
    re.IGNORECASE,
)


def parse_observation(raw: str) -> Observation:
    text = raw.strip()

    if not text:
        raise ValueError("Observation cannot be empty.")

    match = SERVICE_OBSERVATION_PATTERN.fullmatch(text)

    if match is None:
        return Observation(description=text)

    port = int(match.group("port"))
    if not 1 <= port <= 65535:
        return Observation(description=text)

    return Observation(
        description=text,
        service=match.group("service").lower(),
        port=port,
        protocol=match.group("protocol").lower(),
    )
