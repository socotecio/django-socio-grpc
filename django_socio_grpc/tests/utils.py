from contextlib import contextmanager
from unittest.mock import mock_open, patch


@contextmanager
def patch_open(read_data=""):
    m = mock_open(read_data=read_data)

    with patch("io.open", m), patch("builtins.open", m), patch("pathlib.Path.mkdir"), patch(
        "pathlib.Path.open", m
    ):
        yield m
