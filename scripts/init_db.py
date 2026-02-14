"""Initialize the database by creating all tables."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import init_db


async def main():
    """Create all database tables."""
    print("Creating database tables...")
    await init_db()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
