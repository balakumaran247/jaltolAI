from langchain.tools import BaseTool
from src.utils import JaltolBaseClass, EEAsset
from src.prompt import single_year_desc
from src.utils import LocationDetails
from typing import Dict
import ee

ee.Initialize()

topic = "Precipitation or Rainfall"


class Precipitation(JaltolBaseClass):
    PRECIPITATION = "users/jaltolwelllabs/IMD/rain"

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
        self.precipitation = EEAsset(self.PRECIPITATION)

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


class PrecipitationSingleHydrologicalYearSingleVillage(BaseTool):
    name = "Precipitation_Hydrological_Year_Single_Village"
    description = single_year_desc.format(topic, "specific village", "hydrological")

    def _run(self, location: str, year: int) -> Dict[str, Dict[str, Dict[int, float]]]:
        ll = LocationDetails(location)
        ee_location = ll.ee_obj()
        rain = Precipitation(ee_location, year)
        value = rain.handler()
        return {topic: {location: {year: value}}}

    def _arun(self, location: str, year: int):
        raise NotImplementedError("This tool does not support async")
