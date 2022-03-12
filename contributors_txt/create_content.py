import json
import logging
import subprocess
import warnings
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Union

from contributors_txt.const import (
    DEFAULT_TEAM_ROLE,
    GIT_SHORTLOG,
    NO_SHOW_MAIL,
    NO_SHOW_NAME,
)


class Alias(NamedTuple):
    mails: List[str]
    authoritative_mail: Optional[str]
    name: str
    team: str


def get_aliases(aliases_file: Union[Path, str, None], normalize=False) -> List[Alias]:
    aliases: List[Alias] = []
    if aliases_file is None:
        return aliases
    with open(aliases_file, encoding="utf8") as f:
        parsed_aliases = json.load(f)
        for alias in parsed_aliases:
            logging.debug("Alias: %s", alias)
            if isinstance(alias, str):
                if "team" not in parsed_aliases[alias]:
                    parsed_aliases[alias]["team"] = DEFAULT_TEAM_ROLE
                python_alias = Alias(name=alias, **parsed_aliases[alias])
            else:
                if not normalize:
                    warnings.warn(
                        "Using old copyrite format, you should use the configuration "
                        "normalization with 'contributors-txt-normalize-configuration'"
                    )
                if "authoritative_mail" not in alias:
                    alias["authoritative_mail"] = None
                if "team" not in alias:
                    alias["team"] = DEFAULT_TEAM_ROLE
                python_alias = Alias(**alias)
            aliases.append(python_alias)
    return aliases


class Person(NamedTuple):
    number_of_commits: int
    name: str
    mail: Optional[str]
    team: str

    def __gt__(self, other: "Person") -> bool:  # type: ignore[override]
        """Permit sorting contributors by number of commits."""
        return self.number_of_commits.__gt__(other.number_of_commits)

    def __add__(self, other: "Person") -> "Person":  # type: ignore[override]
        assert self.name == other.name, f"{self.name} != {other.name}"
        template = f"Mails are not the same: {self.mail} != {other.mail} for {self} vs {other}:\n"
        template += f'"{self.name}": '
        template += "{"
        mail = self.mail[1:-1] if self.mail is not None else ""
        other_mail = other.mail[1:-1] if other.mail is not None else ""
        template += f"""
            "mails": ["{mail}","{other_mail}"],
            "authoritative_mail": "{mail}"
"""
        if self.team != DEFAULT_TEAM_ROLE:
            template += f',\n"team": "{self.team}"'
        template += "}"
        assert self.mail == other.mail, template
        assert self.team == other.team
        return Person(
            self.number_of_commits + other.number_of_commits,
            self.name,
            self.mail,
            self.team,
        )

    def __str__(self) -> str:
        return f"{self.name} {self.mail}" if self.mail else f"{self.name}"


def create_content(
    aliases: List[Alias], shortlog_output: str, configuration_file: str
) -> str:
    result: str = f"""\
# This file is autogenerated by 'contributors-txt',
# using the configuration in '{configuration_file}'
# please do not modify manually

"""
    persons = persons_from_shortlog(aliases, shortlog_output)
    result += add_teams(persons)
    result += add_contributors(persons)
    return result


def persons_from_shortlog(
    aliases: List[Alias], shortlog_output: str
) -> Dict[str, Person]:
    persons: Dict[str, Person] = {}
    for unparsed_person in shortlog_output.split("\n"):
        if not unparsed_person:
            # Empty line in git output
            continue
        logging.debug("Handling %s", unparsed_person)
        new_person = _parse_person(unparsed_person, aliases)
        if new_person.name in persons:
            new_person = persons[new_person.name] + new_person
        persons[new_person.name] = new_person
    return persons


def add_contributors(persons):
    result = """\
Contributors
------------
"""
    for person in sorted(persons.values(), reverse=True):
        if person.team != DEFAULT_TEAM_ROLE:
            continue
        if person.mail in NO_SHOW_MAIL or person.name in NO_SHOW_NAME:
            continue
        result += f"- {person}\n"
    return result


def add_teams(persons):
    result = ""
    teams = {}
    for person in sorted(persons.values(), reverse=True):
        if person.team != DEFAULT_TEAM_ROLE:
            members = teams.get(person.team, [])
            members.append(person)
            teams[person.team] = members
    if teams:
        for team_name, team_members in teams.items():
            result += f"""\
{team_name}
{len(team_name) * '-'}
"""
            for team_member in team_members:
                result += f"- {team_member}\n"
            result += "\n\n"
    return result


def get_shortlog_output() -> str:
    git_shortlog = subprocess.run(GIT_SHORTLOG, capture_output=True, check=False)
    return git_shortlog.stdout.decode("utf8")


def _parse_person(unparsed_person: str, aliases: List[Alias]) -> Person:
    splitted_person = unparsed_person.split()
    number_of_commit, *names = splitted_person[:-1]
    name = " ".join(names)
    mail: Optional[str] = splitted_person[-1][1:-1]
    team = DEFAULT_TEAM_ROLE
    if mail == "none@none":
        mail = None
    for alias in aliases:
        if mail and mail in alias.mails:
            logging.debug("Found an alias: %s", mail)
            mail = alias.authoritative_mail
            name = alias.name
            team = alias.team
            break
    logging.debug("Person is aliased to %s %s %s", number_of_commit, name, mail)
    return Person(int(number_of_commit), name, f"<{mail}>" if mail else None, team)
