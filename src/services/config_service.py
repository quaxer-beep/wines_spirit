import logging

from src.config.settings import settings
from src.database.connection import db_manager
from src.repositories.config_repository import ConfigRepository

logger = logging.getLogger(__name__)

CONFIG_KEYS = [
    "MPESA_CONSUMER_KEY",
    "MPESA_CONSUMER_SECRET",
    "MPESA_PASSKEY",
    "MPESA_SHORTCODE",
    "MPESA_ENVIRONMENT",
    "MPESA_CALLBACK_URL",
    "ETIMS_ENDPOINT",
    "ETIMS_USERNAME",
    "ETIMS_PASSWORD",
    "SYNC_API_URL",
    "SYNC_API_KEY",
]


class ConfigService:
    def __init__(self):
        self.repo = ConfigRepository()

    def load_all_into_settings(self):
        with db_manager.get_session() as session:
            for key in CONFIG_KEYS:
                value = self.repo.get_value(key, session=session)
                if value is not None:
                    setattr(settings, key, value)
        logger.debug("Loaded %d config values into settings.", len(CONFIG_KEYS))

    def save_mpesa_config(self, consumer_key, consumer_secret, passkey, shortcode, environment):
        with db_manager.get_session() as session:
            self.repo.set_value(session, "MPESA_CONSUMER_KEY", consumer_key)
            self.repo.set_value(session, "MPESA_CONSUMER_SECRET", consumer_secret)
            self.repo.set_value(session, "MPESA_PASSKEY", passkey)
            self.repo.set_value(session, "MPESA_SHORTCODE", shortcode)
            self.repo.set_value(session, "MPESA_ENVIRONMENT", environment)
            session.commit()

        settings.MPESA_CONSUMER_KEY = consumer_key
        settings.MPESA_CONSUMER_SECRET = consumer_secret
        settings.MPESA_PASSKEY = passkey
        settings.MPESA_SHORTCODE = shortcode
        settings.MPESA_ENVIRONMENT = environment
        logger.info("M-Pesa configuration saved.")

    def save_etims_config(self, endpoint, username, password):
        with db_manager.get_session() as session:
            self.repo.set_value(session, "ETIMS_ENDPOINT", endpoint)
            self.repo.set_value(session, "ETIMS_USERNAME", username)
            self.repo.set_value(session, "ETIMS_PASSWORD", password)
            session.commit()

        settings.ETIMS_ENDPOINT = endpoint
        settings.ETIMS_USERNAME = username
        settings.ETIMS_PASSWORD = password
        logger.info("eTIMS configuration saved.")
