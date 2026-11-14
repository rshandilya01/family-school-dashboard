"""Load fictional sample data when the household has no children yet."""

from __future__ import annotations

import os

from app.db import connect, init_db, load_sample


def main() -> None:
    path = os.environ.get("DATABASE_PATH", "data/school.db")
    conn = connect(path)
    init_db(conn)
    message = load_sample(conn)
    print(message or "Loaded fictional sample data.")


if __name__ == "__main__":
    main()
