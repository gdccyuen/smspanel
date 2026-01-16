#!/usr/bin/env python3
"""Mock HKT SMS service provider API for testing.

This script runs a simple Flask server that mimics the HKT SMS API
endpoint for testing purposes without needing real HKT credentials.

Usage:
    python scripts/mock_hkt_api.py

Then in your application, set HKT_BASE_URL to the mock server URL:
    HKT_BASE_URL=http://localhost:5555/gateway/gateway.jsp
"""

from flask import Flask, request, jsonify
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/gateway/gateway.jsp", methods=["POST"])
def mock_hkt_gateway():
    """Mock HKT SMS gateway endpoint.

    Accepts form data with:
        - application: Application ID
        - mrt: Mobile Recipient Number (e.g., "85212345678")
        - sender: Sender number
        - msg_utf8: Message content (UTF-8 encoded)

    Returns:
        Mock HKT API response
    """
    data = request.form
    application = data.get("application", "")
    mrt = data.get("mrt", "")
    sender = data.get("sender", "")
    msg_utf8 = data.get("msg_utf8", "")

    logger.info("[Mock HKT] Received SMS request:")
    logger.info(f"  Application: {application}")
    logger.info(f"  Recipient: {mrt}")
    logger.info(f"  Sender: {sender}")
    logger.info(f"  Message: {msg_utf8}")

    # Simulate failure for specific test scenarios
    # You can add test phone numbers that should fail
    FAIL_TEST_NUMBERS = os.getenv("MOCK_FAIL_NUMBERS", "").split(",")
    if mrt in FAIL_TEST_NUMBERS:
        logger.warning(f"[Mock HKT] Simulating failure for recipient: {mrt}")
        return "ERROR: Failed to send SMS", 400

    # Simulate success response (matches HKT API format)
    # The real HKT API returns a plain text response with status
    response_text = "OK: Message sent successfully"
    logger.info(f"[Mock HKT] Success: {response_text}")
    return response_text, 200


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "mock-hkt-api"}), 200


if __name__ == "__main__":
    # Use port 5555 to avoid conflicts with main app (port 5000)
    port = int(os.getenv("MOCK_HKT_PORT", "5555"))
    host = os.getenv("MOCK_HKT_HOST", "127.0.0.1")
    debug = os.getenv("MOCK_HKT_DEBUG", "false").lower() == "true"

    logger.info(f"Starting Mock HKT SMS API on http://{host}:{port}")
    logger.info(f"Gateway endpoint: http://{host}:{port}/gateway/gateway.jsp")
    logger.info(f"Health check: http://{host}:{port}/health")

    app.run(host=host, port=port, debug=debug)
