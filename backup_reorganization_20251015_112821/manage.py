#!/usr/bin/env python3
"""
CaseStrainer Management Script
==============================

This script provides a command-line interface for common development and
deployment tasks for the CaseStrainer application.
"""

import os
import sys
import subprocess
import click
from flask.cli import FlaskGroup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def create_app():
    """Create and configure the Flask application."""
    from src.app_final_vue import create_app as create_flask_app

    return create_flask_app()


# Initialize Flask application group
cli = FlaskGroup(create_app=create_app)


@cli.command()
def init_db():
    """Initialize the database."""
    from src import db

    click.echo("Creating database tables...")
    db.create_all()
    click.echo("Database initialized successfully!")


@cli.command()
@click.argument("test_names", nargs=-1)
def test(test_names):
    """Run tests with pytest."""
    import pytest

    args = []
    if test_names:
        args.extend(test_names)
    else:
        args = ["tests/"]

    # Add coverage if installed
    try:
        import coverage

        args = [
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html",
        ] + args
    except ImportError:
        click.echo("Coverage not installed. Install with: pip install coverage")

    sys.exit(pytest.main(args))


@cli.command()
@click.option("--host", "-h", default="0.0.0.0", help="The host to bind to.")
@click.option("--port", "-p", default=5000, help="The port to bind to.")
@click.option("--debug/--no-debug", default=None, help="Enable/disable debug mode.")
def run(host, port, debug):
    """Run the development server."""
    if debug is None:
        debug = os.environ.get("FLASK_DEBUG", "1") == "1"

    app = create_app()
    app.run(host=host, port=port, debug=debug)


@cli.command()
def lint():
    """Run code linters."""
    click.echo("Running flake8...")
    flake8 = subprocess.run(["flake8", "src", "tests"])

    click.echo("\nRunning black...")
    black = subprocess.run(["black", "--check", "src", "tests"])

    click.echo("\nRunning isort...")
    isort = subprocess.run(["isort", "--check-only", "src", "tests"])

    if any([flake8.returncode, black.returncode, isort.returncode]):
        click.echo("\nLinting failed! See above for details.")
        sys.exit(1)

    click.echo("\nAll linting passed!")


@cli.command()
def format():
    """Format code with black and isort."""
    click.echo("Running black...")
    subprocess.run(["black", "src", "tests"])

    click.echo("\nRunning isort...")
    subprocess.run(["isort", "src", "tests"])

    click.echo("\nCode formatting complete!")


@cli.command()
@click.argument("command", nargs=-1)
def shell(command):
    """Run a shell command with the application context."""
    from flask import current_app
    import code

    # Prepare local namespace
    local_vars = {
        "app": current_app,
        "db": current_app.extensions.get("sqlalchemy").db,
        "models": __import__("src.models", fromlist=["*"]),
    }

    # If a command was provided, execute it and exit
    if command:
        exec(" ".join(command), globals(), local_vars)
        return

    # Otherwise, start an interactive shell
    banner = (
        "Python {}\n".format(sys.version)
        + "App: {}\n".format(current_app.import_name)
        + "Instance: {}".format(current_app.instance_path)
    )

    try:
        from IPython import embed

        embed(banner1=banner, user_ns=local_vars)
    except ImportError:
        code.interact(banner=banner, local=local_vars)


if __name__ == "__main__":
    cli()
