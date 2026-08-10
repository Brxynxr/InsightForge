from abc import ABC, abstractmethod
from collections.abc import Awaitable

from app.engines.context_models import EngineContext


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
