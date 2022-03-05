import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Union

from contributors_txt.const import GIT_SHORTLOG, NO_SHOW_MAIL, NO_SHOW_NAME


class Alias(NamedTuple):
    mails: List[str]
    authoritative_mail: Optional[str]
    name: str


def get_aliases(aliases_file: Union[Path, str, None]) -> List[Alias]:
    aliases: List[Alias] = []
    if aliases_file is None:
        return aliases
    with open(aliases_file, encoding="utf8") as f:
        for alias in json.load(f):
            if "authoritative_mail" not in alias:
                alias["authoritative_mail"] = None
            aliases.append(Alias(**alias))
    return aliases


class Person(NamedTuple):
    number_of_commits: int
    name: str
    mail: Optional[str]

    def __gt__(self, other: "Person") -> bool:  # type: ignore[override]
        """Permit sorting contributors by number of commits."""
        return self.number_of_commits.__gt__(other.number_of_commits)

    def __add__(self, other: "Person") -> "Person":  # type: ignore[override]
        assert self.name == other.name, f"{self.name} != {other.name}"
        assert (
            self.mail == other.mail
        ), f"""
        "mails": ["{self.mail}","{other.mail}"],
    "authoritative_mail": "{self.mail}",
    "name": "{self.name}"
"""
        return Person(
            self.number_of_commits + other.number_of_commits, self.name, self.mail
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.mail})" if self.mail else f"{self.name}"


def create_content(aliases: List[Alias]) -> str:
    result: str = """\
# This file is autogenerated by 'contributors-txt',
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
