from typing import Dict, Union

import ee
from langchain.tools import BaseTool

from src.prompt import single_year_desc
from src.utils import EEAsset, JaltolBaseClass, LocationDetails

ee.Initialize()

topic = "Evapotranspiration or Actual Evapotranspiration"


class Evapotranspiration(JaltolBaseClass):
    """
    Class for calculating evapotranspiration.

    Attributes:
        EVAPOTRANSPIRATION (str): The asset path for evapotranspiration data.

    """

    EVAPOTRANSPIRATION = "users/jaltolwelllabs/ET/etSSEBop"

    def __init__(
        self,
        location: Union[ee.Geometry, ee.Feature, ee.FeatureCollection],
        year: int,
        temporal_span: str = "hydrological",
        temporal_step: str = "year",
        temporal_reducer: str = "sum",
    ) -> None:
        """
        Initialize the Evapotranspiration instance.

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
        self.precipitation = EEAsset(self.EVAPOTRANSPIRATION)

    def handler(self) -> float:
        """
        Calculate the evapotranspiration.

        Returns:
            float: The evapotranspiration value.

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


class EvapotranspirationSingleHydrologicalYearSingleVillage(BaseTool):
    """
    Tool for calculating evapotranspiration for a specific village in a single hydrological year.

    Attributes:
        name (str): The name of the tool.
        description (str): The description of the tool.

    """

    name = "Evapotranspiration_Hydrological_Year_Single_Village"
    description = single_year_desc.format(topic, "specific village", "hydrological")

    def _run(self, location: str, year: int) -> Dict[str, Dict[str, Dict[int, float]]]:
        """
        Run the tool to calculate evapotranspiration for a specific village in a single hydrological year.

        Args:
            location (str): The name of the location.
            year (int): The year.

        Returns:
            Dict[str, Dict[str, Dict[int, float]]]: The calculated evapotranspiration value.

        """
        ll = LocationDetails(location)
        ee_location = ll.ee_obj()
        et = Evapotranspiration(ee_location, year)
        value = et.handler()
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
