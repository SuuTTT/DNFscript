"""Screen/OCR adapter for the offline renderer, with confidence propagation."""
from .mock_game import MockScreen
from .model import Observation

class OfflineOcr:
    """Deterministic OCR substitute; accepts only MockScreen in Phase 1."""
    def read(self, screen: MockScreen) -> Observation:
        confidence = {token: 0.99 for token in screen.ocr_text}
        if screen.perturbation == "mild_noise": confidence["DECORATIVE_TEXT"] = 0.51
        if screen.perturbation == "low_confidence":
            confidence = {token: 0.44 for token in screen.ocr_text}
        if screen.perturbation == "action_uncertain":
            confidence = {token: 0.93 for token in screen.ocr_text}
        return Observation(screen.ocr_text, confidence, screen.hash, screen.perturbation)
