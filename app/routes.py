from datetime import datetime

from flask import request, Blueprint, jsonify
from marshmallow import ValidationError
from sqlalchemy import select

from app import create_app, db
from app.models import (
    Client,
    Parking,
    ClientParking
)
from app.schemas import (
    ClientSchema,
    ParkingSchema,
    ClientParkingSchema,
)

routes = Blueprint("clients", __name__)


@routes.route("/clients/<int:client_id>", methods=["GET"])
def get_client(client_id: int):
    client = (
        db.session.execute(select(Client).where(Client.id == client_id))
        .scalars()
        .one_or_none()
    )
    if client is None:
        return {"message": "Client not found"}, 404
    return ClientSchema().dump(client), 200

@routes.route("/clients", methods=["GET"])
def get_clients():
    clients = db.session.execute(select(Client)).scalars().all()
    return ClientSchema().dump(clients, many=True), 200


@routes.route("/clients", methods=["POST"])
def create_client():
    schema = ClientSchema()
    try:
        client = schema.load(request.json)

    except ValidationError as exc:
        return exc.messages, 400

    client = Client(**client)
    db.session.add(client)
    db.session.commit()

    return schema.dump(client), 201


@routes.route("/parkings", methods=["POST"])
def create_parking():
    schema = ParkingSchema()
    try:
        parking = schema.load(request.json)

    except ValidationError as exc:
        print(exc.messages)
        return exc.messages, 400

    parking = Parking(**parking)
    db.session.add(parking)
    db.session.commit()

    return schema.dump(parking), 201


@routes.route("/client_parkings", methods=["POST"])
def create_client_parkings():
    schema = ClientParkingSchema()

    try:
        client_parking = schema.load(request.json)
    except ValidationError as exc:
        return exc.messages, 400

    parking = (
        db.session.execute(
            select(Parking).where(Parking.id == client_parking["parking_id"])
        )
        .scalars()
        .one_or_none()
    )

    if parking:

        if parking.opened:

            if parking.count_available_places > 0:

                client = (
                    db.session.execute(
                        select(Client).where(
                            Client.id == client_parking["client_id"]
                        )
                    )
                    .scalars()
                    .one_or_none()
                )

                if client:

                    query = ClientParking(**client_parking)
                    db.session.add(query)
                    parking.count_available_places -= 1
                    db.session.commit()

                    return schema.dump(query), 201

                return jsonify({"error": "Client is not found"}), 404

            return (
                jsonify(
                    {"error": "There are no free places in the parking lot"}
                ),
                404,
            )

        return jsonify({"error": "Parking is closed"}), 404

    return jsonify({"error": "Parking is not found"}), 404


@routes.route("/client_parkings", methods=["DELETE"])
def delete_client_parkings():
    schema = ClientParkingSchema()
    try:
        client_parking = schema.load(request.json)
    except ValidationError as exc:
        return exc.messages, 400

    query = (
        db.session.execute(
            select(ClientParking)
            .where(
                ClientParking.client_id == client_parking["client_id"],
                ClientParking.parking_id == client_parking["parking_id"],
                ClientParking.time_out.is_(None),
            )
            .join(Parking, ClientParking.parking_id == Parking.id)
            .join(Client, ClientParking.client_id == Client.id)
        )
        .scalars()
        .one_or_none()
    )

    if query:

        if query.client and query.client.credit_card and query.parking:
            if query.time_in < datetime.now():
                query.parking.count_available_places += 1
                query.time_out = datetime.now()
                db.session.commit()

                return schema.dump(query), 200

            return (
                jsonify(
                    {
                        "error": "The date of arrival cannot "
                        "be more than the current time"
                    }
                ),
                404,
            )

        return jsonify({"error": "The client does not have a card"}), 404

    return jsonify({"error": "Not found client parking mapping"}), 404


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
