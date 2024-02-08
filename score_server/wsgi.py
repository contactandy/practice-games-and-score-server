"""Main entrypoint for score server."""
import argparse
import logging

from score_server import clear_db, init_app

DATABASE = "scores.db"

app = init_app(DATABASE)


def clear_database():
    clear_db(DATABASE)


def getLogLevels():
    """Return available log level names."""
    try:
        level_names = logging.getLevelNamesMapping().keys()
    except AttributeError:
        # getLevelNamesMapping only present in >= Python3.11
        level_names = list(
            logging.getLevelName(level)
            for level in range(logging.NOTSET, logging.CRITICAL + 1)
        )
        level_names = (level for level in level_names if not level.startswith("Level"))
    return list(level_names)


PARSER = argparse.ArgumentParser(description="Server for logging scores")
PARSER.add_argument("--port", help="Port to use. Defaults to 5000.", default=5000, type=int)
PARSER.add_argument("--host", help="Host IP to use. Defaults to localhost.", default='localhost', type=str)
PARSER.add_argument(
    "--log-level",
    choices=getLogLevels(),
    default="INFO",
    help="Set log level to one of the named levels.",
)


def main():
    """Main entrypoint for score server."""
    args = PARSER.parse_args()

    numeric_level = getattr(logging, args.log_level)
    logging.basicConfig(level=numeric_level)
    logging.info(f"Log level set to {args.log_level}[{numeric_level}]")

    app.run(port=args.port, host=args.host)


if __name__ == "__main__":
    main()
