import shutil

import click

from glyhunter import api, utils
from glyhunter.config import ConfigError
from glyhunter.database import DatabaseError


@click.group()
@click.version_option()
@click.help_option("-h", "--help")
def cli():
    """GlyHunter: A tool for glycan composition annotation and quantification."""


@cli.command()
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Force re-initialization.",
)
def init(force):
    """Initialize GlyHunter."""
    if force:
        click.echo("Re-initializing GlyHunter.")
        api.initiate(force=True)
    else:
        try:
            api.initiate(force=False)
        except FileExistsError:
            msg = (
                "GlyHunter has already been initialized. "
                "Re-initialize and overwrite existing files?"
            )
            if click.confirm(msg, default=False, show_default=True, abort=True):
                api.initiate(force=True)
    click.echo(f"Initialized GlyHunter in {utils.get_glyhunter_dir()}.")


@cli.command()
@click.argument(
    "data_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
)
@click.option(
    "-o",
    "--output",
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    help="Output directory path.",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Configuration file path for this run.",
)
@click.option(
    "-d",
    "--database",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Database file path for this run.",
)
@click.option(
    "--denovo",
    is_flag=True,
    help="Run de novo glycan composition annotation.",
)
def run(data_path, output, config, database, denovo):
    """Run the GlyHunter workflow."""
    if database and denovo:
        raise click.UsageError("Cannot specify both --database and --denovo.")
    click.echo("Running GlyHunter.")
    try:
        output_dir = api.run(data_path, output, config, database, denovo)
    except FileExistsError as e:
        if click.confirm(
            f"Output directory {e.args[0]} already exists. Overwrite?",
            default=False,
            abort=True,
        ):
            shutil.rmtree(e.args[0])
            output_dir = api.run(data_path, output, config, database, denovo)
    else:
        click.echo(f"Results saved to {output_dir}.")


@cli.command()
@click.option(
    "--copy",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Copy the current configuration file to the specified directory.",
)
@click.option(
    "--update",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Update the configuration file.",
)
def config(copy, update):
    """View and update GlyHunter configuration."""
    if copy:
        filepath = api.copy_config(copy)
        click.echo(f"Configuration file copied to {filepath}.")
    if update:
        try:
            api.update_config(update)
        except ConfigError as e:
            raise click.UsageError(str(e))
        else:
            click.echo(f"Configuration file updated from {update}.")


@cli.command()
@click.option(
    "--copy",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Copy the current database file to the specified directory.",
)
@click.option(
    "--update",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Update the database file.",
)
def db(copy, update):
    """View and update GlyHunter database."""
    if copy:
        filepath = api.copy_database(copy)
        click.echo(f"Database copied to {filepath}.")
    if update:
        try:
            api.update_database(update)
        except DatabaseError as e:
            raise click.UsageError(str(e))
        click.echo(f"Database file updated from {update}.")
