from . import BaseDisasterModule

class WildfireModule(BaseDisasterModule):
    def analyze(self, image_tensor, before_image_tensor=None, original_image=None, confidence=None):
        if not self.is_trained:
            return self._get_fallback_response("wildfire", confidence)
        return self._get_fallback_response("wildfire", confidence)
