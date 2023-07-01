from typing import Dict

import ee
from langchain.tools import BaseTool

from src.prompt import single_year_desc
from src.utils import EEAsset, JaltolBaseClass, LocationDetails

ee.Initialize()

topic = "Precipitation or Rainfall"


class Precipitation(JaltolBaseClass):
    """
    Class for calculating precipitation.

    Attributes:
        PRECIPITATION (str): The asset path for precipitation data.

    """

    PRECIPITATION = "users/jaltolwelllabs/IMD/rain"

    def __init__(
        self,
        location: ee.Geometry,
        year: int,
        temporal_span: str = "hydrological",
        temporal_step: str = "year",
        temporal_reducer: str = "sum",
    ) -> None:
        """
        Initialize the Precipitaion instance.

        Args:
            location (Union[ee.Geometry, ee.Feature, ee.FeatureCollection]): The location geometry.
            year (int): The year.
            temporal_span (str): The temporal span (default: "hydrological").
            temporal_step (str): The temporal step (default: "year").
            temporal_reducer (str): The temporal reducer (default: "sum").

        """
        self.geometry = location
        self.year = year
        self.temporal_span = temporal_span
        self.temporal_step = temporal_step
        self.temporal_reducer = temporal_reducer
        self.precipitation = EEAsset(self.PRECIPITATION)

    def handler(self) -> float:
        """
        Calculate the precipitation.

        Returns:
            float: The precipitation value.

        """
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
    """
    Tool for calculating Precipitation for a specific village in a single hydrological year.

    Attributes:
        name (str): The name of the tool.
        description (str): The description of the tool.

    """

    name = "Precipitation_Hydrological_Year_Single_Village"
    description = single_year_desc.format(topic, "specific village", "hydrological")

    def _run(self, location: str, year: int) -> Dict[str, Dict[str, Dict[int, float]]]:
        """
        Run the tool to calculate precipitation for a specific village in a single hydrological year.

        Args:
            location (str): The name of the location.
            year (int): The year.

        Returns:
            Dict[str, Dict[str, Dict[int, float]]]: The calculated precipitation value.

        """
        ll = LocationDetails(location)
        ee_location = ll.ee_obj()
        rain = Precipitation(ee_location, year)
        value = rain.handler()
        return {topic: {location: {year: value}}}

    def _arun(self, location: str, year: int) -> None:
        """
        Asynchronous version of the run method (not implemented).

        Args:
            location (str): The name of the location.
            year (int): The year.

        Raises:
            NotImplementedError: This tool does not support async.

        """
        raise NotImplementedError("This tool does not support async")
