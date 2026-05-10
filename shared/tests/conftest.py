"""Pytest configuration - set environment variables before any test imports."""
import os

# Set DATABASE_URL before any test module imports to allow database.py
# to construct the SQLAlchemy engine (no actual connection is made at import time)
os.environ.setdefault("DATABASE_URL", "mysql+aiomysql://test:test@localhost:3306/test")
