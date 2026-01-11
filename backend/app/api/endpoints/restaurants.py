from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.restaurant import Restaurant
from app.schemas.restaurant import (
    Restaurant as RestaurantSchema,
    RestaurantSearchParams
)
from app.api.endpoints.auth import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.get("", response_model=List[RestaurantSchema])
async def get_restaurants(
    cuisine_type: Optional[str] = None,
    max_distance: Optional[float] = Query(None, description="Maximum distance in km"),
    price_range: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get restaurants with optional filters
    
    - **cuisine_type**: Filter by cuisine (e.g., 'turkish', 'italian')
    - **max_distance**: Maximum distance from campus in km
    - **price_range**: Filter by price range ($, $$, $$$, $$$$)
    - **search**: Search in name, address, or description
    - **limit**: Number of results to return (default: 20, max: 100)
    """
    query = db.query(Restaurant)
    
    # Apply filters
    if cuisine_type:
        query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine_type}%"))
    
    if max_distance is not None:
        query = query.filter(Restaurant.distance_from_campus <= max_distance)
    
    if price_range:
        query = query.filter(Restaurant.price_range == price_range)
    
    if search:
        search_filter = or_(
            Restaurant.name.ilike(f"%{search}%"),
            Restaurant.address.ilike(f"%{search}%"),
            Restaurant.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Order by distance from campus
    query = query.order_by(Restaurant.distance_from_campus.asc())
    
    restaurants = query.limit(limit).all()
    return restaurants


@router.get("/{restaurant_id}", response_model=RestaurantSchema)
async def get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific restaurant by ID"""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    return restaurant


@router.get("/nearby", response_model=List[RestaurantSchema])
async def get_nearby_restaurants(
    max_distance: float = Query(2.0, description="Maximum distance in km"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get restaurants within walking distance of campus"""
    restaurants = db.query(Restaurant).filter(
        Restaurant.distance_from_campus <= max_distance
    ).order_by(
        Restaurant.distance_from_campus.asc()
    ).limit(limit).all()
    
    return restaurants


@router.get("/cuisines", response_model=List[dict])
async def get_cuisine_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available cuisine types with counts"""
    cuisines = db.query(
        Restaurant.cuisine_type,
        func.count(Restaurant.id).label('count')
    ).filter(
        Restaurant.cuisine_type.isnot(None)
    ).group_by(
        Restaurant.cuisine_type
    ).order_by(
        func.count(Restaurant.id).desc()
    ).all()
    
    return [{"cuisine_type": c[0], "count": c[1]} for c in cuisines]
