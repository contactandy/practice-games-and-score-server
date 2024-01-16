"""Test score_server routines."""

import score_server


def test_clear_db(db, db_entries):
    """Test clear_db."""
    # inmemory database should start empty
    cursor = db.cursor()
    # can't use parameter substituion for table name -> no executemany
    for table, values in db_entries.items():
        params_holder = f"({', '.join(len(values)*['?'])})"
        cursor.execute(f"INSERT into {table} VALUES {params_holder};", values)
    entries_by_table = [
        cursor.execute(f"SELECT * FROM {table};").fetchall()
        for table in db_entries.keys()
    ]
    assert all(len(entry) == 1 for entry in entries_by_table)

    score_server.clear_db(db)

    entries_by_table = [
        cursor.execute(f"SELECT * FROM {table};").fetchall()
        for table in db_entries.keys()
    ]
    assert all(entry == [] for entry in entries_by_table)
