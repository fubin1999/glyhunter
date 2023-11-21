from pathlib import Path


def get_glyhunter_dir() -> Path:
    """Return the path to the GlyHunter directory."""
    return Path.home() / ".glyhunter"


def get_db_path() -> Path:
    """Return the path to the database file."""
    return Path.home() / ".glyhunter" / "database.byonic"


def get_config_path() -> Path:
    """Return the path to the configuration file."""
    return Path.home() / ".glyhunter" / "config.yaml"


def output_directory(input_path: str | Path) -> Path:
    """Return the output directory for the given input file."""
    path = Path(input_path).with_name(Path(input_path).stem + "_glyhunter_results")
    path.mkdir(exist_ok=True)
    return path
