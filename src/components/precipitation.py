from src.utils import JaltolBaseClass, EEAsset
import ee

ee.Initialize()
_precipitation = "users/jaltolwelllabs/IMD/rain"


class Precipitation(JaltolBaseClass):
    def __init__(
        self,
        location: ee.Geometry,
        year: int,
        temporal_span: str = "hydrological",
        temporal_step: str = "year",
        temporal_reducer: str = "sum",
    ) -> None:
        self.geometry = location
        self.year = year
        self.temporal_span = temporal_span
        self.temporal_step = temporal_step
        self.temporal_reducer = temporal_reducer
        self.precipitation = EEAsset(_precipitation)

    def handler(self):
        start, end = self.date_gen(self.year, self.temporal_span, self.temporal_step)
        filtered = self.filter_collection(
            self.precipitation.ee_col, start, end, self.geometry
        )
        temp_reduced = self.temporal_reduction(filtered, self.temporal_reducer)
        reduced_dict = self.reduce_regions(
            temp_reduced,
            self.geometry,
            self.precipitation.scale,
            self.precipitation.projection,
        )
        rain = reduced_dict["features"][0]["properties"]["mean"]
        return round(rain, 2)
