import logging
from pathlib import Path

from contributors_txt.migration_copyrite import main

HERE = Path(__file__).parent
contributors_aliases = HERE / ".contributors_aliases.json"
EXPECTED = """{
    "bot": {
        "authoritative_mail": "bot@noreply.github.com",
        "mails": [
            "66853113+pre-commit-ci[bot]@users.noreply.github.com",
            "49699333+dependabot[bot]@users.noreply.github.com"
        ]
    },
    "pre-commit-ci[bot]": {
        "authoritative_mail": "bot@noreply.github.com",
        "mails": [
            "66853113+pre-commit-ci[bot]@users.noreply.github.com"
        ]
    }
}"""


def test_basic(tmp_path, caplog) -> None:
    caplog.set_level(logging.DEBUG)
    output = tmp_path / ".contributors_aliases.json"
    main(["-v", "-a", str(contributors_aliases), "-o", str(output)])
    with open(output, encoding="utf8") as f:
        content = f.read()
    assert content == EXPECTED
    new_output = tmp_path / ".contributors_aliases2.json"
    main(["-v", "-a", str(output), "-o", str(new_output)])
    with open(new_output, encoding="utf8") as f:
        content = f.read()
    assert content == EXPECTED
