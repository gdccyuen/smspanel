"""Validation utilities for SMS composition."""

import re
from typing import Tuple

from smspanel.constants.messages import (
    SMS_ENQUIRY_REQUIRED,
    SMS_ENQUIRY_INVALID,
    SMS_CONTENT_REQUIRED,
    SMS_PHONE_INVALID,
)

PHONE_REGEX = re.compile(r"^\d{4}\s?\d{4}$")
ENQUIRY_REGEX = re.compile(r"^\d{4}\s?\d{4}$")


def validate_enquiry_number(enquiry_number: str) -> Tuple[bool, str]:
    """Validate enquiry number format.

    Args:
        enquiry_number: The enquiry number to validate.

    Returns:
        Tuple of (is_valid, error_message).
        is_valid: True if valid, False otherwise.
        error_message: Error description if invalid, empty string if valid.
    """
    if not enquiry_number:
        return False, SMS_ENQUIRY_REQUIRED
    if not ENQUIRY_REGEX.match(enquiry_number):
        return False, SMS_ENQUIRY_INVALID
    return True, ""


def validate_message_content(content: str) -> Tuple[bool, str]:
    """Validate message content.

    Args:
        content: The message content to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not content:
        return False, SMS_CONTENT_REQUIRED
    return True, ""


def validate_recipients(recipients_input: str) -> Tuple[list[str], list[str]]:
    """Validate and parse recipients.

    Args:
        recipients_input: Raw recipients input (one per line).

    Returns:
        Tuple of (valid_recipients, invalid_numbers).
    """
    recipients = [r.strip() for r in recipients_input.split("\n") if r.strip()]

    valid_recipients = []
    invalid_numbers = []
    for r in recipients:
        if PHONE_REGEX.match(r):
            valid_recipients.append(r)
        else:
            invalid_numbers.append(r)

    return valid_recipients, invalid_numbers


def format_phone_error(invalid_numbers: list[str]) -> str:
    """Format phone number validation error message.

    Args:
        invalid_numbers: List of invalid phone numbers.

    Returns:
        Formatted error message.
    """
    return SMS_PHONE_INVALID.format(invalid_numbers=", ".join(invalid_numbers))
