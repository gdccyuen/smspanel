"""Flask application configuration classes.

Environment Variables:
    Required:
        DATABASE_URL - SQLAlchemy database connection string
        SMS_BASE_URL - SMS gateway URL
        SMS_APPLICATION_ID - SMS API application ID
        SMS_SENDER_NUMBER - SMS sender number

    Optional (with defaults):
        SECRET_KEY - Flask session encryption (default: dev key)
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///sms.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SMS Gateway
    SMS_BASE_URL = os.getenv("SMS_BASE_URL")
    SMS_APPLICATION_ID = os.getenv("SMS_APPLICATION_ID")
    SMS_SENDER_NUMBER = os.getenv("SMS_SENDER_NUMBER")

    # SMS Queue
    SMS_QUEUE_WORKERS = 4
    SMS_QUEUE_MAX_SIZE = 1000


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False

    # SMS Gateway (for testing)
    SMS_BASE_URL = "https://test-sms-gateway.example.com/gateway/gateway.jsp"
    SMS_APPLICATION_ID = "test-app"
    SMS_SENDER_NUMBER = "test-sender"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
