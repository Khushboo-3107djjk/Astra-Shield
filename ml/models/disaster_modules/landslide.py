from . import BaseDisasterModule

class LandslideModule(BaseDisasterModule):
    def analyze(self, image_tensor, before_image_tensor=None, original_image=None, confidence=None):
        if not self.is_trained:
            return self._get_fallback_response("landslide", confidence)
        return self._get_fallback_response("landslide", confidence)
