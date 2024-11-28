import os
import subprocess
import time
from typing import Generator
import pytest
import requests
from dotenv import load_dotenv
from faker import Faker
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from playwright.sync_api import sync_playwright, Browser, Page  # Added necessary imports
from app.models import (
    Base,
    User,
    Addition,
    Subtraction,
    Multiplication,
    Division,
)
from app.schemas import UserData
from app.settings import Settings

# Initialize Faker and Password Hasher
fake = Faker()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Load environment variables
load_dotenv()

# Test Settings
class TestSettings(Settings):
    class Config:
        env_prefix = "TEST_DB_"  # Prefix for test database environment variables

test_settings = TestSettings()

# Define test database URL
TEST_DATABASE_URL = (
    f'postgresql://{test_settings.db_user}:{test_settings.db_password}'
    f'@{test_settings.db_host}:{test_settings.db_port}/{test_settings.db_name}'
)

@pytest.fixture(scope="session")
def engine() -> Generator:
    """
    Creates a SQLAlchemy engine connected to the test database.
    """
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    try:
        yield engine
    finally:
        engine.dispose()

@pytest.fixture(scope="session")
def SessionLocal(engine) -> Generator:
    """
    Creates a sessionmaker bound to the test engine.
    """
    Session = sessionmaker(bind=engine)
    yield Session

@pytest.fixture(scope="session", autouse=True)
def setup_database(engine):
    """
    Creates all tables before tests and drops them after all tests.
    """
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(SessionLocal) -> Generator:
    """
    Provides a SQLAlchemy session for a test and rolls back after the test.
    """
    session = SessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        session.rollback()
        raise e
    finally:
        session.close()

@pytest.fixture(scope="function")
def test_user(db_session) -> User:
    """
    Creates a test user in the database.
    """
    plain_password = fake.password(length=12)
    hashed_password = pwd_context.hash(plain_password + test_settings.salt)
    user = User(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        email=fake.unique.email(),
        username="user" + fake.unique.user_name(),
        password=hashed_password,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_calculations(db_session, test_user):
    """
    Creates a set of test calculations for a test user.
    """
    calculations = [
        Addition(user_id=test_user.id, inputs=[1, 2]),
        Subtraction(user_id=test_user.id, inputs=[10, 5]),
        Multiplication(user_id=test_user.id, inputs=[3, 4]),
        Division(user_id=test_user.id, inputs=[20, 4]),
    ]
    db_session.add_all(calculations)
    db_session.commit()
    return calculations

@pytest.fixture(scope="function")
def create_calculation(db_session, test_user):
    """
    Fixture to dynamically create calculations during tests.
    """
    def _create_calculation(calc_type: str, inputs: list[float]):
        calculation_class = {
            "addition": Addition,
            "subtraction": Subtraction,
            "multiplication": Multiplication,
            "division": Division,
        }.get(calc_type.lower())
        if not calculation_class:
            raise ValueError(f"Unsupported calculation type: {calc_type}")
        calculation = calculation_class(user_id=test_user.id, inputs=inputs)
        db_session.add(calculation)
        db_session.commit()
        return calculation

    return _create_calculation

@pytest.fixture(scope="session")
def fastapi_server():
    """
    Starts the FastAPI server before E2E tests and stops it afterward.
    """
    fastapi_process = subprocess.Popen(["python", "main.py"])
    server_url = "http://127.0.0.1:8000/"
    timeout = 30
    start_time = time.time()

    print("Starting FastAPI server...")

    while time.time() - start_time < timeout:
        try:
            response = requests.get(server_url)
            if response.status_code == 200:
                print("FastAPI server is up and running.")
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    else:
        fastapi_process.terminate()
        raise RuntimeError("FastAPI server failed to start within timeout period.")

    yield
    print("Shutting down FastAPI server...")
    fastapi_process.terminate()
    fastapi_process.wait()
    print("FastAPI server has been terminated.")

@pytest.fixture(scope="session")
def playwright_instance_fixture():
    """
    Manages Playwright's lifecycle.
    """
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def browser(playwright_instance_fixture) -> Browser: # type: ignore
    """
    Launches a Playwright browser instance.
    """
    browser = playwright_instance_fixture.chromium.launch(headless=True)
    yield browser
    browser.close()

@pytest.fixture(scope="function")
def page(browser: Browser) -> Page: # type: ignore
    """
    Provides a new Playwright page for each test.
    """
    page = browser.new_page()
    yield page
    page.close()
