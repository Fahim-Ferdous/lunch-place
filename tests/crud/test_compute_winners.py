from sqlalchemy.orm import Session

from crud import (compute_winner, create_restaurant, create_user, get_winners,
                  vote)
from models import Restaurant, Roles, User
from schemas import RestaurantCreate, UserCreate


def create_dummy_employees(db: Session, n: int) -> list[User]:
    u = []
    for i in range(n):
        u.append(
            create_user(
                db,
                UserCreate(
                    username=f"autouser{i}",
                    email=f"autoemail{i}@email.com",
                    role=Roles.EMPLOYEE,
                    password=f"autopass{i}",
                ),
            )
        )
    return u


def create_dummy_restaurants(db: Session, n: int) -> list[Restaurant]:
    r = []
    for i in range(n):
        r.append(create_restaurant(db, RestaurantCreate(name=f"autorestaurant{i}")))
    return r


def distribute_votes(
    db: Session, dist: list[int]
) -> list[tuple[Restaurant, int, list[User]]]:
    users = create_dummy_employees(db, sum(dist))
    restaurants = create_dummy_restaurants(db, len(dist))
    k = 0

    # Instead of initializing with [], we have to go through all these just to make mypy happy :/
    restaurant_voters: list[tuple[Restaurant, int, list[User]]] = [
        (restaurants[0], 0, [users[0]]),
    ]
    restaurant_voters.clear()

    for i, r in zip(dist, restaurants):
        voters = []
        for u in users[k : k + i]:
            vote(db, u.id, r.id)
            voters.append(u)
        k += i
        restaurant_voters.append((r, len(voters), voters))
    return restaurant_voters


def test_single_winner(db: Session) -> None:
    r = sorted(distribute_votes(db, [4, 3, 3]), key=lambda x: x[1], reverse=True)
    compute_winner(db)

    assert r[0][1] > r[1][1], "Test data does not contain single winner"
    u = max(r, key=lambda x: x[1])
    w = [(v.restaurant_id, v.votes) for v in get_winners(db)]

    assert len(w) == 1, "Could not ensure single winner"
    assert w[0] == (u[0].id, u[1]), "Winner is not the same"


def test_multiple_winners(db: Session) -> None:
    r = sorted(distribute_votes(db, [3, 3, 3, 1]), key=lambda x: x[1], reverse=True)
    compute_winner(db)

    assert r[0][1] == r[1][1] == r[2][1], "Test data does not contain multiple winners"
    u = [(i[0].id, i[1]) for i in r[:3]]
    w = sorted([(v.restaurant_id, v.votes) for v in get_winners(db)])

    assert len(w) == 3, "Could not ensure multuple winner"
    assert w == u, "Winners are not the same"
