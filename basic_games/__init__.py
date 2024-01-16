import argparse

from basic_games import button_masher, good_timing, submission

GAME_CATALOGUE = {
    "masher": {
        "module": button_masher,
        "server_name": "BUTTON",
        "auth_method": "single_use_challenge_response",
    },
    "clicker": {
        "module": good_timing,
        "server_name": "TIMING",
        "auth_method": "basic_digest",
    },
}


def socket(socket_string):
    """Return `(ip/hostname, port)` from `ip/hostname:port` string."""
    addr, port = socket_string.split(":")
    return addr, int(port)


PARSER = argparse.ArgumentParser(description="Play a game to get a high score!")
PARSER.add_argument(
    "--game", choices=GAME_CATALOGUE.keys(), required=True, help="select a game"
)
PARSER.add_argument("--username", required=True, help="enter your username")
PARSER.add_argument(
    "--score-server-addr",
    type=socket,  # only raises ValueErrors so OK as type factory
    default="localhost:5000",
    help="Location of the score server. Format as `ip/hostname:port`. Defaults"
    " to `localhost:5000`.",
)


def main():
    """Main routine for basic-games client."""
    args = PARSER.parse_args()

    score = GAME_CATALOGUE[args.game]["module"].App().run()
    if score is not None:
        print(f"Congrats, {args.username}, you got a score of {score}!")

        score_submit = {
            "game": GAME_CATALOGUE[args.game]["server_name"],
            "score": score,
            "username": args.username,
        }
        auth_method = GAME_CATALOGUE[args.game]["auth_method"]
        submission.attempt_posts_with(args.score_server_addr, auth_method, score_submit)


if __name__ == "__main__":
    main()
