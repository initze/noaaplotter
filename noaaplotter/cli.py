#!/usr/bin/env python3
"""
Main CLI entry point for noaaplotter commands.
This provides a clean command-line interface for the noaaplotter package.
"""

import typer
from typing import Optional

# Create the Typer app
app = typer.Typer(
    name="noaaplotter",
    help="CLI for noaaplotter weather data analysis and plotting",
    no_args_is_help=True,
)

# Import the command modules
from noaaplotter.cli import download_data, plot_daily, plot_monthly

# Add commands to the app
app.command()(download_data)
app.command()(plot_daily)
app.command()(plot_monthly)

if __name__ == "__main__":
    app()