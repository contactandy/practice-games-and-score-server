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


PARSER = argparse.ArgumentParser(description="Play a game to get a high score!")
PARSER.add_argument(
    "--game", choices=GAME_CATALOGUE.keys(), required=True, help="select a game"
)
PARSER.add_argument("--username", required=True, help="enter your username")


def main():
    args = PARSER.parse_args()

    score = GAME_CATALOGUE[args.game]["module"].App().run()
    print(f"Congrats, {args.username}, you got a score of {score}!")

    score_submit = {
        "game": GAME_CATALOGUE[args.game]["server_name"],
        "score": score,
        "username": args.username,
    }
    auth_method = GAME_CATALOGUE[args.game]["auth_method"]
    submission.attempt_posts_with(auth_method, score_submit)


if __name__ == "__main__":
    main()
