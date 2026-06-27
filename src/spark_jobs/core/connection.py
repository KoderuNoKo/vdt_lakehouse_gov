"""
SQLAlchemy connection utilities for the metadata store (ib_metadata schema).

Builds a connection URL from the same env-var-based config used by Spark jobs
(see core.config.load_config), so there is a single source of truth for
database credentials.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import load_config


def build_metadata_url(config: dict | None = None) -> str:
    """Construct a ``postgresql://`` connection URL for the metadata schema.

    Parameters
    ----------
    config : dict, optional
        Output of :func:`core.config.load_config`.  When *None* the config
        is loaded automatically from environment variables.
    """
    if config is None:
        config = load_config()

    user = config["db_user"]
    password = config["db_password"]
    host = config["db_host"]
    port = config["db_port"]
    db_name = config["db_name"]

    return (
        f"postgresql://{user}:{password}@{host}:{port}"
        f"/{db_name}?options=-csearch_path%3Dib_metadata"
    )


def create_engine_from_config(config: dict | None = None):
    """Create a SQLAlchemy :class:`~sqlalchemy.engine.Engine`.

    Parameters
    ----------
    config : dict, optional
        Forwarded to :func:`build_metadata_url`.
    """
    url = build_metadata_url(config)
    return create_engine(url, pool_pre_ping=True)


def create_session(engine) -> Session:
    """Return a new :class:`~sqlalchemy.orm.Session` bound to *engine*."""
    factory = sessionmaker(bind=engine)
    return factory()
