"""Tests for TaskQueue rate limiter integration."""


def test_task_queue_uses_rate_limiter(app):
    """TaskQueue should integrate with rate limiter."""
    from smspanel.services.queue import init_task_queue, get_task_queue

    init_task_queue(app, num_workers=1)
    queue = get_task_queue()

    assert queue.rate_limiter is not None
    assert isinstance(queue.rate_limiter.get_tokens(), float)
