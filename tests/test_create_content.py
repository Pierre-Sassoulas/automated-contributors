import logging

import pytest

from contributors_txt.create_content import create_content


@pytest.mark.parametrize(
    "shortlog_output,expected",
    [
        [
            "1 name <email@net.com>",
            "<email@net.com>",
        ],
        [
            "1 another_name <email@net.com>",
            "- another_name",
        ],
        [
            "\n1 name <aemail@net.com>\n2 another_name <email@net.com>",
            """- another_name <email@net.com>
- name <aemail@net.com>
""",
        ],
    ],
)
def test_basic(shortlog_output: str, expected: str, caplog):
    caplog.set_level(logging.DEBUG)
    result = create_content(aliases=[], shortlog_output=shortlog_output)
    assert expected in result
