from . import BaseDisasterModule

class FloodModule(BaseDisasterModule):
    def analyze(self, image_tensor, before_image_tensor=None, original_image=None, confidence=None):
        if not self.is_trained:
            return self._get_fallback_response("flood", confidence)
        
        # Real implementation would go here
        return self._get_fallback_response("flood", confidence)
