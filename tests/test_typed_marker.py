import os
import smspanel


def test_py_typed_marker_exists():
    """Package should include py.typed marker for type checking."""
    package_dir = os.path.dirname(smspanel.__file__)
    py_typed_path = os.path.join(package_dir, "py.typed")

    assert os.path.exists(py_typed_path), "py.typed marker should exist"


def test_py_typed_marker_is_empty_or_has_comment():
    """py.typed marker should be empty or contain a comment."""
    import smspanel
    import os

    package_dir = os.path.dirname(smspanel.__file__)
    py_typed_path = os.path.join(package_dir, "py.typed")

    with open(py_typed_path) as f:
        content = f.read().strip()

    # Should be empty or have a comment
    assert content == "" or content.startswith("#"), "py.typed should be empty or have comment"


def test_package_marked_as_type_checked():
    """Package should be properly structured for type checking."""
    import smspanel

    # Verify package is importable
    assert smspanel is not None

    # Verify key exports exist
    from smspanel import create_app, db, login_manager

    assert create_app is not None
    assert db is not None
    assert login_manager is not None
