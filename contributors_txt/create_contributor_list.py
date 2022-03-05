"""
Create a file listing the contributors of a git repository.
"""

import argparse
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

HERE = Path(__file__).parent
ALIASES_FILE = HERE / ".copyrigth_aliases.json"
DEFAULT_CONTRIBUTOR_PATH = HERE.parent / "CONTRIBUTORS.txt"
GIT_SHORTLOG = ["git", "shortlog", "--summary", "--numbered", "--email"]
NO_SHOW_MAIL = ["bot@noreply.github.com"]
NO_SHOW_NAME = ["root"]


class Alias(NamedTuple):
    mails: List[str]
    authoritative_mail: Optional[str]
    name: str


class Person(NamedTuple):
    number_of_commit: int
    name: str
    mail: Optional[str]

    def __gt__(self, other: "Person") -> bool:  # type: ignore[override]
        """Permit sorting contributors by number of commit."""
        return self.number_of_commit.__gt__(other.number_of_commit)

    def __add__(self, other: "Person") -> "Person":  # type: ignore[override]
        assert self.name == other.name, f"{self.name} != {other.name}"
        assert self.mail == other.mail, f"{self.mail} != {other.mail}"
        return Person(
            self.number_of_commit + other.number_of_commit, self.name, self.mail
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.mail})" if self.mail else f"{self.name}"


def main(args: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_CONTRIBUTOR_PATH),
        help="Where to output the contributor list",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", default=False, help="Logging or not"
    )
    parsed_args: argparse.Namespace = parser.parse_args(args)
    aliases: List[Alias] = []
    with open(ALIASES_FILE, encoding="utf8") as f:
        for alias in json.load(f):
            if "authoritative_mail" not in alias:
                alias["authoritative_mail"] = None
            aliases.append(Alias(**alias))
    if parsed_args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    content = get_content(aliases)
    with open(parsed_args.output, "w", encoding="utf8") as f:
        f.write(content)


def get_content(aliases: List[Alias]) -> str:
    result: str = f"""\
# This file is autogenerated by {__file__},
# please do not modify manually

Contributors
------------
"""
    git_shortlog = subprocess.run(GIT_SHORTLOG, capture_output=True, check=False)
    persons: Dict[str, Person] = {}
    for unparsed_person in git_shortlog.stdout.decode("utf8").split("\n"):
        if not unparsed_person:
            # Empty line in git output
            continue
        logging.debug("Handling %s", unparsed_person)
        new_person = _parse_person(unparsed_person, aliases)
        if new_person.name in persons:
            new_person = persons[new_person.name] + new_person
        persons[new_person.name] = new_person
    for person in sorted(persons.values(), reverse=True):
        if person.mail in NO_SHOW_MAIL or person.name in NO_SHOW_NAME:
            continue
        result += f"- {person}\n"
    return result


def _parse_person(unparsed_person: str, aliases: List[Alias]) -> Person:
    splitted_person = unparsed_person.split()
    number_of_commit, *names = splitted_person[:-1]
    name = " ".join(names)
    mail: Optional[str] = splitted_person[-1][1:-1]
    if mail == "none@none":
        mail = None
    for alias in aliases:
        if mail and mail in alias.mails:
            logging.debug("Found an alias: %s", mail)
            mail = alias.authoritative_mail
            name = alias.name
            break
    logging.debug("Person is aliased to %s %s %s", number_of_commit, name, mail)
    return Person(int(number_of_commit), name, mail)


if __name__ == "__main__":
    main()
