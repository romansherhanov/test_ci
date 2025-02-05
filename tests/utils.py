from tests.factories import (
    ClientFactory,
    ParkingFactory,
    ClientParkingFactory,
)


def create_client(db):
    client = ClientFactory()
    db.session.commit()
    return client


def create_close_parking(db):
    parking = ParkingFactory(opened=False)
    db.session.commit()
    return parking


def create_parking_no_places(db):
    parking = ParkingFactory(opened=True, count_available_places=0)
    db.session.commit()
    return parking


def create_opened_parking(db):
    parking = ParkingFactory(
        opened=True,
        count_places=10,
        count_available_places=10
    )
    db.session.commit()
    return parking


def create_client_parking(db, client, parking, date_in=None, date_out=None):
    if date_in:
        client_parking = ClientParkingFactory(
            client=client, parking=parking, time_in=date_in, time_out=None
        )
    elif date_out:
        client_parking = ClientParkingFactory(
            client=client, parking=parking, time_out=date_out
        )
    else:
        client_parking = ClientParkingFactory(
            client=client, parking=parking, time_out=None
        )

    db.session.commit()
    return client_parking


def create_client_not_credit_card(db):
    client = ClientFactory(credit_card=None)
    db.session.commit()
    return client


def parking_without_places(db):
    parking = ParkingFactory(count_available_places=0)
    db.session.commit()
    return parking
