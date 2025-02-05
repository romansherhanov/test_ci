from datetime import datetime

from marshmallow import (
    Schema, fields, validates_schema, ValidationError, post_load
)


class ClientSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    surname = fields.Str(required=True)
    credit_card = fields.String(required=False)
    car_number = fields.Str(required=False)


class ParkingSchema(Schema):
    id = fields.Int(dump_only=True)
    address = fields.Str(required=True)
    count_places = fields.Int(required=True)
    count_available_places = fields.Int(required=True)
    opened = fields.Boolean(required=False)

    @validates_schema
    def validate_address_and_places(self, data, **kwargs):
        count_places = data.get("count_places")
        count_available_places = data.get("count_available_places")
        if count_available_places > count_places:
            raise ValidationError(
                f"There can be no more accessible places {count_places}"
            )


class ClientParkingSchema(Schema):
    client_id = fields.Int(required=True)
    parking_id = fields.Int(required=True)
    time_in = fields.DateTime(dump_only=True)
    time_out = fields.DateTime(dump_only=True)

    @post_load
    def add_time_in(self, data, **kwargs):
        if "time_in" not in data:
            data["time_in"] = datetime.now()
        return data
