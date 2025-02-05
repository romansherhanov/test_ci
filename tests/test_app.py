import json
import random
from datetime import datetime, timedelta

from pytest_bdd import given, then

import pytest
from sqlalchemy import func, select

from app.models import (
    Client, Parking, ClientParking
)
from tests.utils import (
    create_client,
    create_close_parking,
    create_parking_no_places,
    create_client_parking,
    create_client_not_credit_card,
)


def test_get_client(client, db, user) -> None:
    response = client.get(f"/clients/{user.id}")
    assert response.status_code == 200
    assert response.json["id"] == user.id
    assert response.json["name"] == user.name
    assert response.json["surname"] == user.surname
    assert response.json["credit_card"] == user.credit_card
    assert response.json["car_number"] == user.car_number


def test_get_clients(client, db, user) -> None:
    user_2 = create_client(db)
    response = client.get("/clients")
    assert response.status_code == 200
    assert response.json[0]["id"] == user.id
    assert response.json[0]["name"] == user.name
    assert response.json[0]["surname"] == user.surname
    assert response.json[0]["credit_card"] == user.credit_card
    assert response.json[0]["car_number"] == user.car_number

    assert response.json[1]["id"] == user_2.id
    assert response.json[1]["name"] == user_2.name
    assert response.json[1]["surname"] == user_2.surname
    assert response.json[1]["credit_card"] == user_2.credit_card
    assert response.json[1]["car_number"] == user_2.car_number


@pytest.mark.parametrize(
    "data",
    [
        {"name": "test_user", "surname": "test_surname"},
        {
            "name": "test_user_2",
            "surname": "test_surname_2",
            "credit_card": "4444 4444 4444 4444",
            "car_number": "B 433 FV 99",
        },
    ],
)
def test_create_client(client, db, data) -> None:
    response = client.post(
        "/clients", data=json.dumps(data), content_type="application/json"
    )

    assert response.status_code == 201
    assert db.session.execute(select(func.count(Client.id))).scalar() == 1
    assert response.json["name"] == data["name"]
    assert response.json["surname"] == data["surname"]
    if data.get("credit_card") and data.get("car_number"):
        assert response.json["credit_card"] == data["credit_card"]
        assert response.json["car_number"] == data["car_number"]


@pytest.mark.parametrize(
    "data",
    [
        {
            "address": "test address",
            "count_places": 100,
            "count_available_places": 100
        },
        {
            "address": "test address",
            "count_places": 10,
            "count_available_places": 5,
            "opened": True,
        },
    ],
)
def test_create_parking(client, db, data) -> None:
    response = client.post(
        "/parkings", data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 201
    assert db.session.execute(select(func.count(Parking.id))).scalar() == 1
    assert response.json["address"] == data["address"]
    assert response.json["count_places"] == data["count_places"]
    assert (response.json["count_available_places"] ==
            data["count_available_places"])
    if not data.get("opened") is None:
        assert response.json["opened"] == data["opened"]


def test_failed_create_parking(client, db) -> None:
    # count_available_places > count_places
    data = {
        "address": "Test Address",
        "count_places": 100,
        "count_available_places": 101,
    }
    response = client.post(
        "/parkings", data=json.dumps(data), content_type="application/json"
    )

    assert response.status_code == 400
    assert response.json == (
        {"_schema": ["There can be no more accessible places 100"]}
    )
    assert db.session.execute(select(func.count(Parking.id))).scalar() == 0


@given("Клиент заезжает на парковку")
def test_create_client_parkings(client, db, user, open_parking) -> None:
    parking_count = open_parking.count_available_places
    data = {"client_id": user.id, "parking_id": open_parking.id}
    response = client.post(
        "/client_parkings",
        data=json.dumps(data),
        content_type="application/json"
    )

    assert response.status_code == 201
    assert db.session.execute(
        select(func.count(ClientParking.client_id))
    ).scalar() == 1
    assert response.json["client_id"] == user.id
    assert response.json["parking_id"] == open_parking.id
    assert response.json["time_out"] is None

    time_in = datetime.fromisoformat(response.json["time_in"])
    assert abs((datetime.now() - time_in).total_seconds()) <= 5
    assert parking_count - 1 == open_parking.count_available_places


@pytest.mark.parametrize("data", [{"client_id": 999, "parking_id": 999}])
def test_failed_create_client_parkings_lack_of_client_or_parking(
    client, db, open_parking, data
) -> None:
    response = client.post(
        "/client_parkings",
        data=json.dumps(data),
        content_type="application/json"
    )
    assert response.status_code == 404
    assert response.json["error"] == "Parking is not found"

    data["parking_id"] = open_parking.id
    response = client.post(
        "/client_parkings",
        data=json.dumps(data),
        content_type="application/json"
    )
    assert response.status_code == 404
    assert response.json["error"] == "Client is not found"
    assert db.session.execute(
        select(func.count(ClientParking.client_id))
    ).scalar() == 0


def test_failed_create_client_parkings_close_parking_is_closed(
    client, db, user
) -> None:
    parking = create_close_parking(db)
    parking_count = parking.count_available_places
    data = {"client_id": user.id, "parking_id": parking.id}

    response = client.post(
        "/client_parkings",
        data=json.dumps(data),
        content_type="application/json"
    )
    assert response.status_code == 404
    assert response.json["error"] == "Parking is closed"
    assert parking_count == parking.count_available_places


def test_failed_create_client_parkings_no_places(client, db, user) -> None:
    parking = create_parking_no_places(db)
    parking_count = parking.count_available_places

    data = {"client_id": user.id, "parking_id": parking.id}

    response = client.post(
        "/client_parkings",
        data=json.dumps(data),
        content_type="application/json"
    )
    assert response.status_code == 404
    assert (response.json["error"] ==
            "There are no free places in the parking lot")
    assert db.session.execute(
        select(func.count(ClientParking.client_id))
    ).scalar() == 0
    assert parking_count == parking.count_available_places


@then("Клиент выезжает с парковки")
def test_delete_client_parkings(client, db, user, open_parking) -> None:
    parking_count = open_parking.count_available_places
    client_parking = create_client_parking(
        db=db,
        client=user,
        parking=open_parking
    )
    assert db.session.execute(
        select(func.count(ClientParking.client_id))
    ).scalar() == 1

    data = {"client_id": user.id, "parking_id": open_parking.id}

    response = client.delete(
        "/client_parkings",
        data=json.dumps(data),
        content_type="application/json"
    )
    assert response.status_code == 200
    assert db.session.execute(
        select(func.count(ClientParking.client_id))
    ).scalar() == 1
    assert response.json["client_id"] == user.id
    assert response.json["parking_id"] == open_parking.id
    assert datetime.fromisoformat(
        response.json["time_in"]
    ) == client_parking.time_in

    time_out = datetime.fromisoformat(response.json["time_out"])
    assert abs((datetime.now() - time_out).total_seconds()) <= 5

    assert parking_count + 1 == open_parking.count_available_places


def test_failed_delete_client_parkings_not_card(
        client, db, open_parking
) -> None:
    user = create_client_not_credit_card(db)
    create_client_parking(
        db=db,
        client=user,
        parking=open_parking
    )
    parking_count = open_parking.count_available_places
    assert db.session.execute(
        select(func.count(ClientParking.client_id))
    ).scalar() == 1

    data = {"client_id": user.id, "parking_id": open_parking.id}

    response = client.delete(
        "/client_parkings",
        data=json.dumps(data),
        content_type="application/json"
    )
    assert response.status_code == 404
    assert response.json["error"] == "The client does not have a card"
    assert db.session.execute(
        select(func.count(ClientParking.client_id))
    ).scalar() == 1
    assert parking_count == open_parking.count_available_places


def test_failed_delete_client_parkings_not_mapping(
    client, db, user, open_parking
) -> None:
    parking_count = open_parking.count_available_places
    assert db.session.execute(
        select(func.count(ClientParking.client_id))
    ).scalar() == 0

    data = {"client_id": user.id, "parking_id": open_parking.id}

    response = client.delete(
        "/client_parkings",
        data=json.dumps(data),
        content_type="application/json"
    )
    assert response.status_code == 404
    assert response.json["error"] == "Not found client parking mapping"
    assert db.session.execute(
        select(func.count(ClientParking.client_id))
    ).scalar() == 0
    assert parking_count == open_parking.count_available_places


def test_failed_delete_client_parkings_mapping_in_date_out(
    client, db, user, open_parking
) -> None:
    parking_count = open_parking.count_available_places
    create_client_parking(
        db=db, client=user, parking=open_parking, date_out=datetime.now()
    )
    assert db.session.execute(
        select(func.count(ClientParking.client_id))
    ).scalar() == 1

    data = {"client_id": user.id, "parking_id": open_parking.id}

    response = client.delete(
        "/client_parkings",
        data=json.dumps(data),
        content_type="application/json"
    )
    assert response.status_code == 404
    assert response.json["error"] == "Not found client parking mapping"
    assert db.session.execute(
        select(func.count(ClientParking.client_id))
    ).scalar() == 1
    assert parking_count == open_parking.count_available_places


def test_failed_delete_client_parkings_mapping_over_date_in(
    client, db, user, open_parking
) -> None:
    parking_count = open_parking.count_available_places
    create_client_parking(
        db=db,
        client=user,
        parking=open_parking,
        date_in=datetime.now() + timedelta(hours=random.randint(1, 12)),
    )
    assert db.session.execute(
        select(func.count(ClientParking.client_id))
    ).scalar() == 1

    data = {"client_id": user.id, "parking_id": open_parking.id}

    response = client.delete(
        "/client_parkings",
        data=json.dumps(data),
        content_type="application/json"
    )
    assert response.status_code == 404
    assert (
        response.json["error"]
        == "The date of arrival cannot be more than the current time"
    )
    assert db.session.execute(
        select(func.count(ClientParking.client_id))
    ).scalar() == 1
    assert parking_count == open_parking.count_available_places
