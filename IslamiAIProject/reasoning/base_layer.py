"""
reasoning/base_layer.py
─────────────────────────────────────────────────────────────────
Kontrak dasar untuk semua 7 layer reasoning IslamiAI.
Sama dengan v2, diperluas dengan IslamicLayerContext.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time
import logging

logger = logging.getLogger("islamiai.reasoning")


@dataclass
class LayerResult:
    layer_id: str
    payload: Dict[str, Any]
    confidence: float
    execution_time_ms: float
    warnings: List[str] = field(default_factory=list)
    requires_reprocess: bool = False
    # Khusus IslamiAI: apakah layer ini menyentuh data agama sensitif?
    contains_religious_content: bool = False


class LayerException(Exception):
    def __init__(self, layer_id: str, reason: str, recoverable: bool = True):
        self.layer_id = layer_id
        self.reason = reason
        self.recoverable = recoverable
        super().__init__(f"[{layer_id}] {reason}")


class BaseLayer(ABC):

    @property
    @abstractmethod
    def layer_id(self) -> str:
        pass

    @property
    def required_keys(self) -> List[str]:
        return ["input"]

    @abstractmethod
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def validate_input(self, state: Dict[str, Any]) -> None:
        missing = [k for k in self.required_keys if k not in state]
        if missing:
            raise LayerException(
                self.layer_id,
                f"Missing required keys: {missing}",
                recoverable=False
            )

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.validate_input(state)
        t0 = time.perf_counter()

        try:
            payload = self.process(state)
        except LayerException:
            raise
        except Exception as e:
            raise LayerException(self.layer_id, str(e)) from e

        elapsed_ms = (time.perf_counter() - t0) * 1000

        result = LayerResult(
            layer_id=self.layer_id,
            payload=payload,
            confidence=payload.pop("_confidence", 0.0),
            execution_time_ms=round(elapsed_ms, 3),
            warnings=payload.pop("_warnings", []),
            requires_reprocess=payload.pop("_requires_reprocess", False),
            contains_religious_content=payload.pop("_religious_content", False),
        )

        state[self.layer_id] = result

        logger.debug(
            "%-40s | conf=%.3f | %.1fms | reprocess=%s",
            self.layer_id, result.confidence,
            result.execution_time_ms, result.requires_reprocess
        )
        return state
