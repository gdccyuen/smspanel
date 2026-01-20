"""SMS service configuration."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SMSConfig:
    """SMS service configuration."""

    base_url: str
    application_id: str
    sender_number: str


class ConfigService:
    """Service for managing SMS configuration."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        application_id: Optional[str] = None,
        sender_number: Optional[str] = None,
    ):
        """Initialize config service.

        Args:
            base_url: SMS API base URL.
            application_id: SMS application ID.
            sender_number: SMS sender number.
        """
        self.base_url = base_url
        self.application_id = application_id
        self.sender_number = sender_number

    def get_sms_config(
        self, default_base_url: str = "https://cst01.1010.com.hk/gateway/gateway.jsp"
    ) -> SMSConfig:
        """Get SMS configuration with defaults applied.

        Args:
            default_base_url: Default SMS base URL.

        Returns:
            SMSConfig object.
        """
        return SMSConfig(
            base_url=self.base_url or default_base_url,
            application_id=self.application_id or "LabourDept",
            sender_number=self.sender_number or "852520702793127",
        )
