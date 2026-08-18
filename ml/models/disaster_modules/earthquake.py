from . import BaseDisasterModule

class EarthquakeModule(BaseDisasterModule):
    def analyze(self, image_tensor, before_image_tensor=None, original_image=None, confidence=None):
        if not self.is_trained:
            return self._get_fallback_response("earthquake", confidence)
        return self._get_fallback_response("earthquake", confidence)
