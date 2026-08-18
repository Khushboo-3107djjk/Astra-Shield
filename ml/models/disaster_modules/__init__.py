import json

class BaseDisasterModule:
    """Base interface for all disaster-specific analysis modules."""
    
    def __init__(self, model_path=None, device='cpu'):
        self.device = device
        self.model_path = model_path
        self.is_trained = False
        self.load_model()
        
    def load_model(self):
        """Override to load specific model weights if they exist."""
        pass
        
    def analyze(self, image_tensor, before_image_tensor=None, original_image=None, confidence=None):
        """
        Analyze the image(s) and return standard JSON structure.
        """
        return self._get_fallback_response("unknown", confidence)
        
    def _get_fallback_response(self, disaster_type, confidence=None):
        """Return standardized response when real analysis cannot be performed."""
        return {
            "disaster_type": disaster_type,
            "confidence": confidence,
            "severity": {
                "level": None,
                "score": None
            },
            "affected_area_km2": None,
            "change_percent": None,
            "mask_path": None,
            "analysis_status": "model_not_available",
            "data_source": "demo"
        }
