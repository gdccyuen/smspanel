"""API SMS endpoints."""

from flask import Blueprint, request

from smspanel import db
from smspanel.models import User, Message, Recipient
from smspanel.services.queue import get_task_queue
from smspanel.utils.sms_helper import process_single_sms_task, process_bulk_sms_task
from smspanel.api.responses import APIResponse, unauthorized, bad_request, service_unavailable, not_found
from smspanel.api.decorators import validate_json

api_sms_bp = Blueprint("api_sms", __name__)


def get_user_from_token() -> User | None:
    """Get user from API token.

    Returns:
        User object or None if invalid.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]

    return User.query.filter_by(token=token).first()


@api_sms_bp.route("/sms", methods=["GET"])
def list_messages() -> tuple:
    """List all messages for the authenticated user.

    Query parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 20)

    Returns:
        JSON response with messages list.
    """
    user = get_user_from_token()
    if user is None:
        return unauthorized()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    messages = (
        Message.query.filter_by(user_id=user.id)
        .order_by(Message.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return APIResponse.success(
        data={
            "messages": [
                {
                    "id": m.id,
                    "content": m.content,
                    "status": m.status,
                    "created_at": m.created_at.isoformat(),
                    "recipient_count": m.recipient_count,
                    "recipients": [r.phone for r in m.recipients],
                }
                for m in messages.items
            ],
            "total": messages.total,
            "pages": messages.pages,
            "current_page": page,
        }
    )


@api_sms_bp.route("/sms", methods=["POST"])
@validate_json(["recipient", "content"])
def send_sms() -> tuple:
    """Send a single SMS message (asynchronous).

    Request body (JSON):
        recipient: str - Phone number
        content: str - Message content

    Returns:
        JSON response with message details (status will be 'pending').
    """
    user = get_user_from_token()
    if user is None:
        return unauthorized()

    data = request.get_json()
    recipient = data.get("recipient")
    content = data.get("content")

    # Create message record
    message = Message(user_id=user.id, content=content, status="pending")
    db.session.add(message)
    db.session.flush()

    # Create recipient record
    recipient_record = Recipient(message_id=message.id, phone=recipient, status="pending")
    db.session.add(recipient_record)
    db.session.commit()

    # Enqueue background task
    task_queue = get_task_queue()
    enqueued = task_queue.enqueue(process_single_sms_task, message.id, recipient)

    if not enqueued:
        return service_unavailable()

    return APIResponse.success(
        data={
            "id": message.id,
            "status": "pending",
            "recipient": recipient,
            "content": content,
            "created_at": message.created_at.isoformat(),
        },
        message="SMS queued for sending",
        status_code=202,
    )


@api_sms_bp.route("/sms/send-bulk", methods=["POST"])
@validate_json(["recipients", "content"])
def send_bulk_sms() -> tuple:
    """Send SMS messages to multiple recipients (asynchronous).

    Request body (JSON):
        recipients: list[str] - List of phone numbers
        content: str - Message content

    Returns:
        JSON response with message details (status will be 'pending').
    """
    user = get_user_from_token()
    if user is None:
        return unauthorized()

    data = request.get_json()
    recipients = data.get("recipients", [])
    content = data.get("content")

    # Additional validation for non-empty recipients list
    if not recipients:
        return bad_request("Recipients list cannot be empty", "MISSING_FIELDS")

    # Create message record
    message = Message(user_id=user.id, content=content, status="pending")
    db.session.add(message)
    db.session.flush()

    # Create recipient records
    for recipient in recipients:
        recipient_record = Recipient(message_id=message.id, phone=recipient, status="pending")
        db.session.add(recipient_record)

    db.session.commit()

    # Enqueue background task
    task_queue = get_task_queue()
    enqueued = task_queue.enqueue(process_bulk_sms_task, message.id, recipients)

    if not enqueued:
        return service_unavailable()

    return APIResponse.success(
        data={
            "id": message.id,
            "status": "pending",
            "total": len(recipients),
            "content": content,
            "created_at": message.created_at.isoformat(),
        },
        message="Bulk SMS queued for sending",
        status_code=202,
    )


@api_sms_bp.route("/sms/<int:message_id>", methods=["GET"])
def get_message(message_id: int) -> tuple:
    """Get details of a specific message.

    Args:
        message_id: Message ID

    Returns:
        JSON response with message details.
    """
    user = get_user_from_token()
    if user is None:
        return unauthorized()

    message = Message.query.filter_by(id=message_id, user_id=user.id).first()
    if message is None:
        return not_found("Message not found")

    return APIResponse.success(
        data={
            "id": message.id,
            "content": message.content,
            "status": message.status,
            "created_at": message.created_at.isoformat(),
            "sent_at": message.sent_at.isoformat() if message.sent_at else None,
            "hkt_response": message.hkt_response,
            "recipient_count": message.recipient_count,
            "success_count": message.success_count,
            "failed_count": message.failed_count,
        }
    )


@api_sms_bp.route("/sms/<int:message_id>/recipients", methods=["GET"])
def get_message_recipients(message_id: int) -> tuple:
    """Get recipient details for a specific message.

    Args:
        message_id: Message ID

    Returns:
        JSON response with recipient details.
    """
    user = get_user_from_token()
    if user is None:
        return unauthorized()

    message = Message.query.filter_by(id=message_id, user_id=user.id).first()
    if message is None:
        return not_found("Message not found")

    recipients = [
        {
            "id": r.id,
            "phone": r.phone,
            "status": r.status,
            "error_message": r.error_message,
        }
        for r in message.recipients
    ]

    return APIResponse.success(data={"recipients": recipients})
