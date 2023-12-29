from flask import Flask

app = Flask(__name__)

from basic_games.score_server.app import routes
