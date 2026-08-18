from enum import Enum
from typing import List, Any
from pydantic import BaseModel, Field

class GeometryType(str, Enum):
    POLYGON = "Polygon"
    MULTIPOLYGON = "MultiPolygon"
    LINESTRING = "LineString"
    MULTILINESTRING = "MultiLineString"
    POINT = "Point"

class GeoJSONGeometry(BaseModel):
    """
    GeoJSON-compatible geometry schema for representing areas on Leaflet/MapLibre.
    """
    type: GeometryType = Field(..., description="The type of the geometry, e.g., Polygon or MultiPolygon")
    coordinates: List[Any] = Field(..., description="The coordinates of the geometry in standard GeoJSON format")
