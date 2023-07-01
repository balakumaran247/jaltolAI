from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Tuple, Union

import ee
from geopy.geocoders import Nominatim
from pydantic import BaseModel

# Initialize GEE library
ee.Initialize()


class JaltolInput(BaseModel):
    """
    Represents the input data for the Jaltol endpoint.

    Attributes:
        user (str): The user information.

    """

    user: str


class JaltolOutput(BaseModel):
    """
    Represents the output data from the Jaltol endpoint.

    Attributes:
        text (str): The text output.

    """

    text: str


class LocationDetails:
    """
    Provides location details and utilities.

    Attributes:
        location_name (str): The name of the location.

    """

    def __init__(self, location_name) -> None:
        self.location_name = location_name

    def coordinates(self) -> Union[Tuple[float, float], None]:
        """
        Retrieves the latitude and longitude coordinates of the location.

        Returns:
            Union[Tuple[float, float], None]: The latitude and longitude coordinates, or None if not found.

        """
        geolocator = Nominatim(user_agent="JaltolAI")
        location = geolocator.geocode(self.location_name)
        return (location.latitude, location.longitude) if location else None

    def ee_obj(self) -> ee.FeatureCollection:
        """
        Returns the Earth Engine object for the location.

        Returns:
            ee.FeatureCollection: The Earth Engine object for the location.

        Raises:
            ValueError: If the coordinates are not available.

        """
        if coordinates := self.coordinates():
            latitude, longitude = coordinates
        else:
            raise ValueError
        # return ee.Geometry.Point([longitude, latitude])
        return ee.FeatureCollection(ee.Geometry.Point([longitude, latitude]))

    def admin_details(self):
        pass


@dataclass()
class EEAsset:
    """
    Represents an Earth Engine asset.

    Attributes:
        asset_path (str): The path to the Earth Engine asset.

    """

    asset_path: str
    ee_col: ee.ImageCollection = field(init=False)
    scale: float = field(init=False)
    projection: ee.Projection = field(init=False)

    def __post_init__(self):
        self.ee_col = ee.ImageCollection(self.asset_path)
        self.scale = self.fetch_scale(self.asset_path)
        self.projection = ee.Projection(self.fetch_projection(self.asset_path))

    @classmethod
    def fetch_projection(cls, asset_path: str) -> str:
        """
        Fetches the projection of an Earth Engine asset.

        Args:
            asset_path (str): The path to the Earth Engine asset.

        Returns:
            str: The projection of the asset.

        """
        image = ee.ImageCollection(asset_path).first()
        proj = image.projection().getInfo()
        return proj["crs"]

    @classmethod
    def fetch_scale(cls, asset_path: str) -> float:
        """
        Fetches the scale of an Earth Engine asset.

        Args:
            asset_path (str): The path to the Earth Engine asset.

        Returns:
            float: The scale of the asset.

        """
        image = ee.ImageCollection(asset_path).first()
        return image.projection().nominalScale().getInfo()


class JaltolBaseClass:
    """
    Base class for the Jaltol algorithm.

    Attributes:
        ee_reducer (Dict[str, ee.Reducer]): Mapping of reducer names to Earth Engine reducers.

    """

    ee_reducer = {"mean": ee.Reducer.mean(), "sum": ee.Reducer.sum()}

    def date_gen(
        self,
        year: int,
        temporal_span: str = "hydrological",
        temporal_step: str = "year",
    ) -> Tuple[ee.Date, ee.Date]:
        """
        Generates the start and end dates for a given year and temporal parameters.

        Args:
            year (int): The year.
            temporal_span (str): The temporal span (default: "hydrological").
            temporal_step (str): The temporal step (default: "year").

        Returns:
            Tuple[ee.Date, ee.Date]: The start and end dates.

        """

        def yearly_date(year: int, month: int) -> Tuple[ee.Date, ee.Date]:
            return (
                ee.Date.fromYMD(year, month, 1),
                ee.Date.fromYMD(year + 1, month, 1),
            )

        if temporal_step == "year" and temporal_span == "hydrological":
            return yearly_date(year, 6)
        if temporal_step == "year" and temporal_span == "calendar":
            return yearly_date(year, 1)

    def filter_collection(
        self,
        image_col: ee.ImageCollection,
        start_date: ee.Date,
        end_date: ee.Date,
        geometry: Union[ee.Geometry, ee.Feature, ee.FeatureCollection] = None,
    ) -> ee.ImageCollection:
        """
        Filters an Earth Engine image collection based on date and geometry.

        Args:
            image_col (ee.ImageCollection): The Earth Engine image collection.
            start_date (ee.Date): The start date.
            end_date (ee.Date): The end date.
            geometry (Union[ee.Geometry, ee.Feature, ee.FeatureCollection], optional): The geometry for spatial filtering.

        Returns:
            ee.ImageCollection: The filtered image collection.

        """
        if geometry:
            return image_col.filterDate(start_date, end_date).filterBounds(geometry)
        else:
            return image_col.filterDate(start_date, end_date)

    def temporal_reduction(
        self, image_col: ee.ImageCollection, temporal_reducer: str
    ) -> ee.Image:
        """
        Performs temporal reduction on an Earth Engine image collection.

        Args:
            image_col (ee.ImageCollection): The Earth Engine image collection.
            temporal_reducer (str): The temporal reducer to use.

        Returns:
            ee.Image: The temporally reduced image.

        """
        return image_col.reduce(self.ee_reducer[temporal_reducer])

    def reduce_regions(
        self,
        image: ee.Image,
        geometry: Union[ee.Geometry, ee.Feature, ee.FeatureCollection],
        scale: float,
        projection: ee.Projection,
        spatial_reducer: str = "mean",
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Reduces an Earth Engine image over regions defined by a geometry.

        Args:
            image (ee.Image): The Earth Engine image.
            geometry (Union[ee.Geometry, ee.Feature, ee.FeatureCollection]): The region geometry.
            scale (float): The scale for reduction.
            projection (ee.Projection): The projection for reduction.
            spatial_reducer (str, optional): The spatial reducer to use (default: "mean").

        Returns:
            Dict[str, List[Dict[str, Any]]]: The reduced values for each region.

        """
        return (
            ee.Image(image)
            .reduceRegions(
                collection=geometry,
                reducer=self.ee_reducer[spatial_reducer],
                scale=scale,
                crs=projection,
            )
            .getInfo()
        )  # get_info['features'][0]['properties']
