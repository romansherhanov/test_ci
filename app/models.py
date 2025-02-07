from app import db
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import backref, relationship


class Client(db.Model): # type: ignore
    __tablename__ = "client"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    surname = Column(String(50), nullable=False)
    credit_card = Column(String(50))
    car_number = Column(String(10))

    def __repr__(self):
        return f"Клиент {self.name}"


class Parking(db.Model): # type: ignore
    __tablename__ = "parking"

    id = Column(Integer, primary_key=True)
    address = Column(String(100), nullable=False)
    opened = Column(Boolean)
    count_places = Column(Integer, nullable=False)
    count_available_places = Column(Integer, nullable=False)

    def __repr__(self):
        return f"Паркинг {self.address}"


class ClientParking(db.Model): # type: ignore
    __tablename__ = "client_parking "
    __table_args = UniqueConstraint("client_id", "parking_id")

    client_id = Column(Integer, ForeignKey("client.id"), primary_key=True)
    parking_id = Column(Integer, ForeignKey("parking.id"), primary_key=True)
    time_in = Column(DateTime)
    time_out = Column(DateTime)

    client = relationship(
        "Client",
        backref=backref("client_parking", lazy=True)
    )
    parking = relationship(
        "Parking",
        backref=backref("client_parking", lazy=True)
    )
