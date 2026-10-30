"""Tests for Alembic database migrations upgrade and downgrade."""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_alembic_migrations_upgrade_and_downgrade(tmp_path: Path) -> None:
    db_file = tmp_path / "migration_test.db"
    db_url = f"sqlite:///{db_file}"

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # Test upgrade to head
    command.upgrade(alembic_cfg, "head")
    assert os.path.exists(db_file)

    # Test downgrade to base
    command.downgrade(alembic_cfg, "base")
