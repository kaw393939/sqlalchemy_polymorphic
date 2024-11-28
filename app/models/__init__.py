from abc import ABC, abstractmethod, ABCMeta
from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.declarative import DeclarativeMeta


# Define a custom metaclass combining DeclarativeMeta and ABCMeta
class MyMeta(DeclarativeMeta, ABCMeta):
    pass


# Create the declarative base with the custom metaclass
Base = declarative_base(metaclass=MyMeta)


# Define the SQLAlchemy User model with UUID as primary key
class User(Base):
    __tablename__ = 'users'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # UUID primary key
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Hashed password
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship with Calculation
    calculations = relationship(
        "Calculation",
        back_populates="user",
        cascade="all, delete, delete-orphan"
    )

    def __repr__(self):
        return f"<User(name={self.first_name} {self.last_name}, email={self.email})>"


# Define the SQLAlchemy Calculation base model with polymorphism and ABC
class Calculation(Base, ABC):
    __tablename__ = 'calculations'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # UUID primary key
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)  # Foreign key to User
    type = Column(String(50), nullable=False)  # Type of calculation (e.g., "addition", "subtraction")
    inputs = Column(JSON, nullable=False)  # JSON field to store inputs as a list
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship with User
    user = relationship("User", back_populates="calculations")

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'calculation',
        'with_polymorphic': '*',
    }

    @classmethod
    def create(cls, calculation_type: str, user_id: uuid.UUID, inputs: list[float]) -> 'Calculation':
        """
        Factory method to create Calculation instances based on the calculation type.
        """
        calculation_classes = {
            'addition': Addition,
            'subtraction': Subtraction,
            'multiplication': Multiplication,
            'division': Division,
        }
        calculation_class = calculation_classes.get(calculation_type.lower())
        if not calculation_class:
            raise ValueError(f"Unsupported calculation type: {calculation_type}")
        return calculation_class(user_id=user_id, inputs=inputs)

    @abstractmethod
    def get_result(self) -> float:
        """
        Abstract method to compute the result of the calculation.
        Must be implemented by all subclasses.
        """
        pass

    def __repr__(self):
        return f"<Calculation(type={self.type}, inputs={self.inputs})>"


# Subclass for Addition
class Addition(Calculation):
    __mapper_args__ = {
        'polymorphic_identity': 'addition',
    }

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        return sum(self.inputs)


# Subclass for Subtraction
class Subtraction(Calculation):
    __mapper_args__ = {
        'polymorphic_identity': 'subtraction',
    }

    def get_result(self) -> float:
        if not isinstance(self.inputs, list) or len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        result = self.inputs[0]
        for value in self.inputs[1:]:
            result -= value
        return result


# Subclass for Multiplication
class Multiplication(Calculation):
    __mapper_args__ = {
        'polymorphic_identity': 'multiplication',
    }

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        result = 1
        for value in self.inputs:
            result *= value
        return result


# Subclass for Division
class Division(Calculation):
    __mapper_args__ = {
        'polymorphic_identity': 'division',
    }

    def get_result(self) -> float:
        if not isinstance(self.inputs, list) or len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        result = self.inputs[0]
        for value in self.inputs[1:]:
            if value == 0:
                raise ValueError("Cannot divide by zero.")
            result /= value
        return result
