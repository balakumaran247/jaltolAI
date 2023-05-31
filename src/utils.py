from pydantic import BaseModel
from dataclasses import dataclass, field
from geopy.geocoders import Nominatim
from typing import List, Union, Generator, Tuple, Dict, Any
import ee

# Initialize GEE library
ee.Initialize()

def fetch_projection(asset_path: str) -> str:
    image = ee.ImageCollection(asset_path).first()
    proj = image.projection().getInfo()
    return proj['crs']

def fetch_scale(asset_path: str) -> float:
    image = ee.ImageCollection(asset_path).first()
    return image.projection().nominalScale().getInfo()

class JaltolInput(BaseModel):
    user: str


class LocationDetails:
    def __init__(self, location_name) -> None:
        self.location_name = location_name

    def coordinates(self):
        geolocator = Nominatim(user_agent="my-app")
        location = geolocator.geocode(self.location_name)
        return (location.latitude, location.longitude) if location else None

    def ee_obj(self):
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
    asset_path: str
    ee_col: ee.ImageCollection = field(init=False)
    scale: float = field(init=False)
    projection: ee.Projection = field(init=False)
    
    def __post_init__(self):
        self.ee_col = ee.ImageCollection(self.asset_path)
        self.scale = fetch_scale(self.asset_path)
        self.projection = ee.Projection(fetch_projection(self.asset_path))

class JaltolBaseClass:
    ee_reducer = {
        'mean': ee.Reducer.mean(),
        'sum' : ee.Reducer.sum()
    }
    
    def date_gen(
        self,
        year: int,
        temporal_span: str = 'hydrological',
        temporal_step: str = 'year',
        ) -> Tuple[ee.Date, ee.Date]:
        
        def yearly_date(year: int, month: int) -> Tuple[ee.Date, ee.Date]:
            return (ee.Date.fromYMD(year,month,1), ee.Date.fromYMD(year+1,month,1))
        
        if temporal_step == 'year' and temporal_span == 'hydrological':
            return yearly_date(year, 6)
        if temporal_step == 'year' and temporal_span == 'calendar':
            return yearly_date(year, 1)
    
    def filter_collection(
        self,
        image_col: ee.ImageCollection,
        start_date: ee.Date,
        end_date: ee.Date,
        geometry: Union[ee.Geometry, ee.Feature, ee.FeatureCollection] = None
        ):
        if geometry:
            return image_col.filterDate(start_date, end_date).filterBounds(geometry)
        else:
            return image_col.filterDate(start_date, end_date)
    
    def temporal_reduction(
        self,
        image_col: ee.ImageCollection,
        temporal_reducer: str):
        return image_col.reduce(self.ee_reducer[temporal_reducer])
    
    def reduce_regions(
        self,
        image: ee.Image,
        geometry: Union[ee.Geometry, ee.Feature, ee.FeatureCollection],
        scale: float,
        projection: ee.Projection,
        spatial_reducer: str = 'mean',
        ) -> Dict[str,List[Dict[str,Any]]]:
        return ee.Image(image).reduceRegions(
            collection= geometry,
            reducer= self.ee_reducer[spatial_reducer],
            scale= scale,
            crs= projection
            ).getInfo() # get_info['features'][0]['properties']