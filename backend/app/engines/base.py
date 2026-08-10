from abc import ABC, abstractmethod
from collections.abc import Awaitable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EngineContext:
    """Shared context passed through the processing pipeline."""

    batch_id: str = ""
    batch_index: int = 0
    total_batches: int = 0
    records: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    results: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)


class BaseEngine(ABC):
    """Base class for all processing engines.

    Every engine MUST expose exactly one public execution method:
        execute(context) -> EngineContext

    Each engine receives, processes, and returns context
    without modifying external state.
    """

    @abstractmethod
    def execute(self, context: EngineContext) -> EngineContext | Awaitable[EngineContext]:
        """Execute the engine's responsibility on the given context.
        Can be sync or async.
        """
        ...
