import math
from dataclasses import dataclass, field
from enum import Enum, auto

MAX_BACKOFF_INTERVAL = 300  # 5 mins


class ServerState(Enum):
    UNKNOWN = auto()
    ONLINE = auto()
    DEGRADED = auto()
    OFFLINE = auto()


class LatencyTier(Enum):
    GOOD = (0, 300, "🟢 Good", 0x57F287)
    MILD = (300, 500, "🟡 Mild lag", 0xFEE75C)
    SEVERE = (500, 750, "🟠 Severe lag", 0xE67E22)
    UNPLAYABLE = (750, float("inf"), "🔴 Unplayable", 0xED4245)

    def __init__(self, low: float, high: float, label: str, color: int):
        self.low = low
        self.high = high
        self.label = label
        self.color = color

    @classmethod
    def classify(cls, ms: float) -> "LatencyTier":
        return next(t for t in reversed(cls) if ms > t.low)

    def format(self, ms: float) -> str:
        return f"{self.label} ({ms:.0f}ms)"


@dataclass
class MonitoredServer:
    channel_id: int
    guild_id: int
    address: str
    port: int = 25565
    query_port: int = 25565
    interval: int = 60

    state: ServerState = field(default=ServerState.UNKNOWN, init=False)
    players_online: set[str] = field(default_factory=set, init=False)
    _latency_tier: LatencyTier = field(default=LatencyTier.GOOD, init=False)
    _status_fails: int = field(default=0, init=False)
    _query_fails: int = field(default=0, init=False)
    _last_poll: float = field(default=0.0, init=False)
    _polling: bool = field(default=False, init=False)

    STATUS_FAIL_THRESHOLD: int = 2
    QUERY_FAIL_THRESHOLD: int = 3

    @property
    def effective_interval(self) -> float:
        if self._status_fails <= self.STATUS_FAIL_THRESHOLD:
            return float(self.interval)
        steps = self._status_fails - self.STATUS_FAIL_THRESHOLD
        return min(self.interval * math.pow(2, steps), MAX_BACKOFF_INTERVAL)
