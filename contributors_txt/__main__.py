"""
Create a file listing the contributors of a git repository.
"""

import argparse
import logging
from pathlib import Path
from typing import List, Optional, Union

from contributors_txt.const import DEFAULT_CONTRIBUTOR_PATH
from contributors_txt.create_content import create_content, get_aliases


def main(args: Optional[List[str]] = None) -> None:
    parsed_args = parse_args(args)
    create_contributors_txt(
        parsed_args.aliases, parsed_args.output, parsed_args.verbose
    )


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument(
        "-a",
        "--aliases",
        default=None,
        help="The path to the aliases file.",
    )
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
    return parsed_args


def create_contributors_txt(
    aliases_file: Union[Path, str], output: Union[Path, str], verbose: bool
) -> None:
    aliases = get_aliases(aliases_file)
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    content = create_content(aliases)
    with open(output, "w", encoding="utf8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
