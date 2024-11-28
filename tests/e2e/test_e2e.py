import pytest
from playwright.sync_api import Page

@pytest.mark.e2e
def test_hello_world(page: Page, fastapi_server):
    """
    Test that the homepage displays "Hello World".
    """
    # Navigate to the homepage and ensure the page is fully loaded
    page.goto('http://localhost:8000', wait_until="networkidle")

    # Wait for the <h1> element to appear
    page.wait_for_selector('h1')

    # Assert the main header displays the expected text
    assert page.inner_text('h1') == 'Hello World', "Homepage did not display 'Hello World'."


@pytest.mark.e2e
def test_calculator_add(page: Page, fastapi_server):
    """
    Test the addition functionality of the calculator.
    """
    # Navigate to the homepage and ensure the page is fully loaded
    page.goto('http://localhost:8000', wait_until="networkidle")

    # Wait for the input fields and the button to appear
    page.wait_for_selector('#a')
    page.wait_for_selector('#b')
    page.wait_for_selector('button:text("Add")')

    # Fill in the first number
    page.fill('#a', '10')

    # Fill in the second number
    page.fill('#b', '5')

    # Click the "Add" button
    page.click('button:text("Add")')

    # Wait for the result to be updated
    page.wait_for_selector('#result')

    # Assert the result is as expected
    assert page.inner_text('#result') == 'Result: 15', "Addition result was not correct."


@pytest.mark.e2e
def test_calculator_divide_by_zero(page: Page, fastapi_server):
    """
    Test the divide by zero functionality of the calculator.
    """
    # Navigate to the homepage and ensure the page is fully loaded
    page.goto('http://localhost:8000', wait_until="networkidle")

    # Wait for the input fields and the button to appear
    page.wait_for_selector('#a')
    page.wait_for_selector('#b')
    page.wait_for_selector('button:text("Divide")')

    # Fill in the first number
    page.fill('#a', '10')

    # Fill in the second number with 0 to simulate division by zero
    page.fill('#b', '0')

    # Click the "Divide" button
    page.click('button:text("Divide")')

    # Wait for the result to be updated
    page.wait_for_selector('#result')

    # Assert the error message is displayed as expected
    assert page.inner_text('#result') == 'Error: Cannot divide by zero!', "Division by zero did not return the correct error message."
