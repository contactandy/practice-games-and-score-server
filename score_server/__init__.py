"""Provides app factory."""
import sqlite3

from flask import Flask

from score_server import routes


def init_db(conn):
    """Create tables with the provided database connection."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT UNIQUE,
            created TIMESTAMP 
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS button (
            username TEXT UNIQUE,
            score INTEGER DEFAULT 0, 
            date DATETIME
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS timing ( 
            username TEXT UNIQUE, 
            score FLOAT NOT NULL, 
            date DATETIME 
        );
        """
    )
    conn.commit()


def clear_db(conn):
    """Clear the database of entries"""
    tables = ["tokens", "timing", "button"]
    # can't use parameter substituion for table name -> no executemany
    for table in tables:
        conn.execute(f"DELETE FROM {table};")


def init_app(database):
    """Initialize the application."""
    app = Flask(__name__)
    app.config["DB"] = database

    with sqlite3.connect(database) as scores:
        init_db(scores)

    app.register_blueprint(routes.scoreboard)
    return app
