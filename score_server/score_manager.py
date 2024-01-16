"""Module for handling score submissions."""
import logging

SCORE_COMPARISONS_BY_GAME = {
    "BUTTON": {"select": max, "cast": int},
    "TIMING": {"select": min, "cast": float},
}


def insert_or_update_score(conn, score_entry):
    """
    Update the given database with the given score.

    If given score is 'better' than the one in the database, update the entry
    with the new score. Either way, update the time played. Determining if an
    entry is better requires a game-specific score selection function and a
    game-specific type function for scores that come in as strings.
    """
    logging.debug(f"score update info: {score_entry}")
    game = score_entry["game"].upper()
    select = SCORE_COMPARISONS_BY_GAME[game]["select"]
    cast = SCORE_COMPARISONS_BY_GAME[game]["cast"]
    username = score_entry["username"]
    score = score_entry["score"]

    cursor = conn.cursor()

    try:
        [old_score] = cursor.execute(
            f"SELECT score FROM {game} WHERE username = ?;", (username,)
        ).fetchone()
        logging.debug(f"found existing entry for username: {old_score}")
    except TypeError:
        # queries with no results return `None` instead of `[]`
        replace_score = score
    else:
        replace_score = select(cast(old_score), cast(score))

    insert_sql = f"""
        INSERT OR REPLACE INTO {game} 
        (username, score, date)
        VALUES (?, ?, datetime())
    """
    cursor.execute(insert_sql, (username, replace_score))
