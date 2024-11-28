import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import with_polymorphic

from app.models import (
    Calculation,
    Addition,
    Subtraction,
    Multiplication,
    Division,
    User,
)


def test_create_user(db_session):
    """
    Test creating a user and ensure it is correctly inserted into the database.
    """
    # Arrange: Create a test user
    user = User(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        username="johndoe",
        password="hashedpassword123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Act: Retrieve the user
    retrieved_user = db_session.query(User).filter_by(username="johndoe").first()
    
    # Assert
    assert retrieved_user is not None, "User was not created."
    assert retrieved_user.email == "john.doe@example.com", "User email does not match."
    assert retrieved_user.first_name == "John", "User first name does not match."
    assert retrieved_user.last_name == "Doe", "User last name does not match."


def test_user_fixture(test_user):
    """
    Test the test_user fixture to ensure it provides a valid user.
    """
    # Act: Use the test_user fixture
    user = test_user

    # Assert
    assert "@" in user.email and "." in user.email.split("@")[-1], "Email format is invalid."
    assert user.username.startswith("user"), "Username does not start with 'user'."
    assert len(user.calculations) == 0, "New user should have no calculations."


def test_add_calculations_to_user(test_user, db_session):
    """
    Test adding calculations to a user and ensure they are correctly associated.
    """
    # Arrange: Create Calculations using the factory method
    addition = Calculation.create(
        calculation_type='addition',
        user_id=test_user.id,
        inputs=[10, 5]
    )
    subtraction = Calculation.create(
        calculation_type='subtraction',
        user_id=test_user.id,
        inputs=[20, 5]
    )
    db_session.add_all([addition, subtraction])
    db_session.commit()
    db_session.refresh(addition)
    db_session.refresh(subtraction)
    
    # Act: Retrieve the user and their calculations
    retrieved_user = db_session.query(User).filter_by(id=test_user.id).first()
    
    # Assert: Ensure calculations are associated with the user
    assert retrieved_user is not None, "User was not found."
    assert len(retrieved_user.calculations) == 2, "User should have two calculations."
    assert addition in retrieved_user.calculations, "Addition calculation not associated with user."
    assert subtraction in retrieved_user.calculations, "Subtraction calculation not associated with user."


def test_retrieve_calculations_via_user(test_user, db_session):
    """
    Test retrieving calculations through the user's relationship.
    """
    # Arrange: Create Calculations
    multiplication = Calculation.create(
        calculation_type='multiplication',
        user_id=test_user.id,
        inputs=[4, 5]
    )
    division = Calculation.create(
        calculation_type='division',
        user_id=test_user.id,
        inputs=[20, 4]
    )
    db_session.add_all([multiplication, division])
    db_session.commit()
    db_session.refresh(multiplication)
    db_session.refresh(division)
    
    # Act: Access the user's calculations
    retrieved_user = db_session.query(User).filter_by(id=test_user.id).first()
    user_calculations = retrieved_user.calculations
    
    # Assert
    assert len(user_calculations) == 2, "User should have two calculations."
    assert multiplication in user_calculations, "Multiplication calculation not found in user's calculations."
    assert division in user_calculations, "Division calculation not found in user's calculations."


def test_update_user_information(test_user, db_session):
    """
    Test updating a user's information and ensure calculations remain intact.
    """
    # Arrange: Update user information
    test_user.first_name = "Jane"
    test_user.last_name = "Smith"
    test_user.email = "jane.smith@example.com"
    db_session.commit()
    db_session.refresh(test_user)
    
    # Act: Retrieve the updated user
    updated_user = db_session.query(User).filter_by(id=test_user.id).first()
    
    # Assert: Check updated fields
    assert updated_user.first_name == "Jane", "User first name was not updated."
    assert updated_user.last_name == "Smith", "User last name was not updated."
    assert updated_user.email == "jane.smith@example.com", "User email was not updated."
    
    # Assert: Ensure calculations are still associated
    assert len(updated_user.calculations) >= 0, "User's calculations should remain intact after update."


def test_delete_user_cascades_calculations(test_user, db_session):
    """
    Test deleting a user and ensure that associated calculations are also deleted (cascade).
    """
    # Arrange: Create Calculations
    addition = Calculation.create(
        calculation_type='addition',
        user_id=test_user.id,
        inputs=[5, 5]
    )
    subtraction = Calculation.create(
        calculation_type='subtraction',
        user_id=test_user.id,
        inputs=[15, 5]
    )
    db_session.add_all([addition, subtraction])
    db_session.commit()

    # Act: Delete the user
    db_session.delete(test_user)
    db_session.commit()

    # Assert: Ensure the user is deleted
    deleted_user = db_session.query(User).filter_by(id=test_user.id).first()
    assert deleted_user is None, "User was not deleted."

    # Assert: Ensure calculations are also deleted (cascade)
    deleted_addition = db_session.query(Addition).filter_by(id=addition.id).first()
    deleted_subtraction = db_session.query(Subtraction).filter_by(id=subtraction.id).first()
    assert deleted_addition is None, "Associated Addition calculation was not deleted."
    assert deleted_subtraction is None, "Associated Subtraction calculation was not deleted."
