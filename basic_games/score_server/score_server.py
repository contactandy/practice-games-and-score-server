"""Entrypoint for running score server"""
from basic_games.score_server.app import app


def main():
    app.run()


if __name__ == "__main__":
    app.run()
