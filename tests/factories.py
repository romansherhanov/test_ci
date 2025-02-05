import random
import string
from datetime import timedelta

import factory
from faker import Faker

from app import db
from app.models import (
    Client, ClientParking, Parking
)

fake = Faker("ru_RU")


class ClientFactory(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        model = Client
        sqlalchemy_session = db.session

    name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    credit_card = factory.LazyAttribute(lambda x: fake.credit_card_provider())
    car_number = factory.LazyAttribute(
        lambda x: f""
        f"{random.choice(string.ascii_uppercase)}"
        f"{random.randint(100, 999)}"
        f"{random.choice(string.ascii_uppercase)}"
        f"{random.choice(string.ascii_uppercase)} "
        f"{random.randint(1, 99)}"
    )


class ParkingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Parking
        sqlalchemy_session = db.session

    address = factory.LazyAttribute(lambda x: fake.address())
    opened = factory.Faker("boolean")
    count_places = factory.LazyAttribute(lambda x: random.randrange(0, 100))
    count_available_places = factory.LazyAttribute(
        lambda x: random.randrange(0, 100)
    )


class ClientParkingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ClientParking
        sqlalchemy_session = db.session

    client_id = factory.SubFactory(ClientFactory)
    parking_id = factory.SubFactory(ParkingFactory)
    time_in = factory.Faker("date_time_this_year")
    time_out = factory.LazyAttribute(
        lambda obj: obj.time_in + timedelta(hours=random.randint(1, 12))
    )
