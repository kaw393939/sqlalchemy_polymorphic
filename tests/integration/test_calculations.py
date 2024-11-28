import pytest
from sqlalchemy.orm import with_polymorphic
from app.models import (
    Calculation,
    Addition,
    Subtraction,
    Multiplication,
    Division,
)


@pytest.mark.parametrize("calculation_type, inputs, expected_result", [
    ('addition', [10, 5], 15),
    ('subtraction', [20, 5], 15),
    ('multiplication', [4, 5], 20),
    ('division', [20, 4], 5),
])
def test_create_calculation(test_user, db_session, calculation_type, inputs, expected_result):
    """
    Test creating various types of Calculations using the factory method.
    """
    # Arrange: Use the factory method to create a Calculation instance
    calculation = Calculation.create(
        calculation_type=calculation_type,
        user_id=test_user.id,
        inputs=inputs
    )
    
    # Act: Add and commit the Calculation to the database
    db_session.add(calculation)
    db_session.commit()
    db_session.refresh(calculation)
    
    # Assert: Ensure the Calculation is correctly inserted
    assert calculation.id is not None, "Calculation ID should be set."
    assert calculation.user_id == test_user.id, "Calculation is not linked to the correct user."
    assert calculation.inputs == inputs, f"Calculation inputs should be {inputs}."
    assert calculation.get_result() == expected_result, f"Calculation result should be {expected_result}."
    
    # Assert: Ensure the calculation is an instance of the correct subclass
    if calculation_type == 'addition':
        assert isinstance(calculation, Addition), "Calculation is not an instance of Addition."
    elif calculation_type == 'subtraction':
        assert isinstance(calculation, Subtraction), "Calculation is not an instance of Subtraction."
    elif calculation_type == 'multiplication':
        assert isinstance(calculation, Multiplication), "Calculation is not an instance of Multiplication."
    elif calculation_type == 'division':
        assert isinstance(calculation, Division), "Calculation is not an instance of Division."


def test_create_unsupported_calculation_type(test_user, db_session):
    """
    Test that creating a Calculation with an unsupported type raises a ValueError.
    """
    # Arrange: Define an unsupported calculation type
    unsupported_type = 'modulus'
    
    # Act & Assert: Attempt to create a Calculation and expect a ValueError
    with pytest.raises(ValueError, match=f"Unsupported calculation type: {unsupported_type}"):
        calculation = Calculation.create(
            calculation_type=unsupported_type,
            user_id=test_user.id,
            inputs=[10, 3]
        )
        db_session.add(calculation)
        db_session.commit()


@pytest.mark.parametrize("inputs", [
    [10, 0],  # Division by zero
])
def test_division_by_zero(test_user, db_session, inputs):
    """
    Test that dividing by zero raises a ValueError.
    """
    # Arrange: Use the factory method to create a Division instance with inputs including zero
    division = Calculation.create(
        calculation_type='division',
        user_id=test_user.id,
        inputs=inputs
    )
    db_session.add(division)
    db_session.commit()
    db_session.refresh(division)
    
    # Act & Assert: Attempt to compute the result and expect a ValueError
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        division.get_result()


def test_update_calculation(test_user, db_session):
    """
    Test updating an existing Calculation.
    """
    # Arrange: Create and insert a Calculation using the factory method
    multiplication = Calculation.create(
        calculation_type='multiplication',
        user_id=test_user.id,
        inputs=[2, 3]
    )
    db_session.add(multiplication)
    db_session.commit()
    db_session.refresh(multiplication)
    
    # Act: Update the Calculation's inputs
    multiplication.inputs = [5, 7]
    db_session.commit()
    db_session.refresh(multiplication)
    
    # Assert: Ensure the Calculation has been updated correctly
    assert multiplication.inputs == [5, 7], "Calculation inputs were not updated correctly."
    assert multiplication.get_result() == 35, "Multiplication result was not updated correctly."


def test_delete_calculation(test_user, db_session):
    """
    Test deleting a Calculation from the database.
    """
    # Arrange: Create and insert a Calculation using the factory method
    division = Calculation.create(
        calculation_type='division',
        user_id=test_user.id,
        inputs=[20, 4]
    )
    db_session.add(division)
    db_session.commit()
    db_session.refresh(division)
    
    # Act: Delete the Calculation
    db_session.delete(division)
    db_session.commit()
    
    # Assert: Ensure the Calculation has been deleted
    deleted_calculation = db_session.query(Division).filter_by(id=division.id).first()
    assert deleted_calculation is None, "Calculation was not deleted."
    
    # Optionally, verify the relationship from the user side
    assert division not in test_user.calculations, "Deleted calculation still present in user's calculations."


def test_polymorphic_query(test_user, db_session):
    """
    Test that polymorphic queries retrieve all Calculation subclasses correctly.
    """
    # Arrange: Insert multiple Calculations of different types
    calculations = [
        Calculation.create('addition', test_user.id, [1, 2]),
        Calculation.create('subtraction', test_user.id, [5, 3]),
        Calculation.create('multiplication', test_user.id, [4, 6]),
        Calculation.create('division', test_user.id, [10, 2]),
    ]
    db_session.add_all(calculations)
    db_session.commit()
    
    # Act: Perform a polymorphic query to retrieve all Calculations
    CalculationWithSubclasses = with_polymorphic(
        Calculation,
        [Addition, Subtraction, Multiplication, Division]
    )
    retrieved_calculations = db_session.query(CalculationWithSubclasses).filter_by(user_id=test_user.id).all()
    
    # Assert: Ensure all Calculations are retrieved and of correct types
    assert len(retrieved_calculations) == 4, "Incorrect number of calculations retrieved."
    for calc in calculations:
        # Find the retrieved calculation with the same ID
        retrieved_calc = next((rc for rc in retrieved_calculations if rc.id == calc.id), None)
        assert retrieved_calc is not None, f"Calculation {calc.id} was not retrieved."
        assert isinstance(retrieved_calc, type(calc)), f"Retrieved calculation type mismatch for {calc.id}."
        assert retrieved_calc.get_result() == calc.get_result(), f"Calculation result mismatch for {calc.id}."
