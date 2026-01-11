from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RestaurantBase(BaseModel):
    """Base restaurant schema"""
    name: str = Field(..., description="Restaurant name")
    category: Optional[str] = Field(None, description="Category (restaurant, cafe, fast_food, bar, pub)")
    cuisine_type: Optional[str] = Field(None, description="Type of cuisine")
    address: Optional[str] = Field(None, description="Full address")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    phone: Optional[str] = Field(None, description="Phone number")
    website: Optional[str] = Field(None, description="Website URL")
    opening_hours: Optional[str] = Field(None, description="Opening hours")
    description: Optional[str] = Field(None, description="Description")
    osm_id: str = Field(..., description="OpenStreetMap ID")
    distance_from_campus: Optional[float] = Field(None, description="Distance from campus in km")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags/features")
    rating: Optional[float] = Field(None, description="Rating")
    price_range: Optional[str] = Field(None, description="Price range")


class RestaurantCreate(RestaurantBase):
    """Schema for creating a restaurant"""
    pass


class Restaurant(RestaurantBase):
    """Complete restaurant schema with ID and timestamps"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RestaurantSearchParams(BaseModel):
    """Search parameters for restaurants"""
    query: Optional[str] = Field(None, description="Search query")
    category: Optional[str] = Field(None, description="Filter by category")
    cuisine_type: Optional[str] = Field(None, description="Filter by cuisine type")
    max_distance: Optional[float] = Field(None, description="Maximum distance from campus in km")
    min_rating: Optional[float] = Field(None, description="Minimum rating")
    price_range: Optional[str] = Field(None, description="Price range filter")
    limit: int = Field(10, description="Number of results", ge=1, le=100)
    offset: int = Field(0, description="Offset for pagination", ge=0)
