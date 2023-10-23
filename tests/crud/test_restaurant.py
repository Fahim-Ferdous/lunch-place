from sqlalchemy.orm import Session

import crud
from models import Weekdays
from schemas import RestaurantCreate


def test_create_restaurant_creates_empty_daily_menus(db: Session) -> None:
    r = crud.create_restaurant(
        db, RestaurantCreate(name="someTestRestaurant1", description="description")
    )

    assert len(r.daily_menus) == 7
    assert all(
        [
            i.day == j
            for i, j in zip(
                sorted(r.daily_menus, key=lambda x: x.day), sorted(Weekdays)
            )
        ]
    )
