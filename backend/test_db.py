"""Storage layer: schema init + settings round-trip (PRD §9 data model)."""

import db


def test_init_and_settings():
    db.init_db()
    db.set_setting("test_key", "test_value")
    assert db.get_setting("test_key") == "test_value"
    assert db.get_setting("missing_key", "dflt") == "dflt"
    db.set_setting("test_key", "v2")
    assert db.get_setting("test_key") == "v2"
    with db.connect() as conn:
        conn.execute("DELETE FROM settings WHERE key='test_key'")
        conn.commit()
