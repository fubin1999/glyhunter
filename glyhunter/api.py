import importlib.resources as res
from pathlib import Path
from typing import Optional

from glyhunter import utils
from glyhunter.config import Config, load_config
from glyhunter.database import Database, load_database, DatabaseError
from glyhunter.denovo import DeNovoEngine
from glyhunter.mass_list import MassList
from glyhunter.results_export import write_mass_list_results, write_summary_tables
from glyhunter.search import search_many


def initiate(force: bool = False) -> None:
    """Initialize GlyHunter.

    Create a .glyhunter directory in the user's home directory and populate it
    with the database and configuration files. If the directory already exists,
    raise an error when force is False, and overwrite the files when force is
    True.

    Args:
        force: Force re-initialization.

    Raises:
        FileExistsError: When the .glyhunter directory already exists and force
            is False.
    """
    try:
        utils.get_glyhunter_dir().mkdir()
    except FileExistsError:
        if not force:
            raise FileExistsError(
                f"GlyHunter directory {utils.get_glyhunter_dir()} already exists. "
                "Set force to True to overwrite."
            )
    db_res_path = res.files("glyhunter").joinpath("resources/database.byonic")
    config_res_path = res.files("glyhunter").joinpath("resources/config.yaml")
    with open(utils.get_db_path(), "w", encoding="utf8") as f:
        f.write(db_res_path.read_text(encoding="utf8"))
    with open(utils.get_config_path(), "w", encoding="utf8") as f:
        f.write(config_res_path.read_text(encoding="utf8"))


def run(
    input_path: str | Path,
    output_path: Optional[str | Path] = None,
    config_path: Optional[str | Path] = None,
    db_path: Optional[str | Path] = None,
    denovo: bool = False,
    all_candidates: bool = False
) -> Path:
    """Run GlyHunter.

    Args:
        input_path: Path to input file or directory.
        output_path: Path to output directory, optional. Default to the directory with the
            same name as the input file, with an additional "_glyhunter_results.
        config_path: Path to configuration file, optional. Default to the config file in
            the GlyHunter directory.
        db_path: Path to database file, optional. Default to the database file in the
            GlyHunter directory.
        denovo: Whether to perform de novo search. Default: False.
        all_candidates: Whether to output all candidates, rather than the
            one with most similar m/z. Default: False.

    Returns:
        Path to output directory.
    """
    output_path = Path(output_path) if output_path else utils.output_directory(input_path)
    if output_path.exists():
        raise FileExistsError(output_path)
    output_path.mkdir()

    config = load_config(config_path)

    if denovo:
        search_engine = DeNovoEngine(
            charge_carrier=config["charge_carrier"],
            reducing_end=config["reducing_end"],
            modifications=config["modifications"],
            constraints=config["constraints"],
            global_mod_constraints=config["global_modification_constraints"],
        )
    else:
        search_engine = load_database(
            db_path,
            charge_carrier=config["charge_carrier"],
            reducing_end=config["reducing_end"],
            modifications=config["modifications"],
            global_mod_constraints=config["global_modification_constraints"],
        )

    mass_lists = MassList.from_flex_analysis(input_path)
    if config["calibration_on"]:
        for mass_list in mass_lists:
            mass_list.calibrate(config["calibration_by"], config["calibration_tol"])

    results = search_many(
        mass_lists, search_engine, config["mz_tol"], all_candidates=all_candidates
    )

    write_mass_list_results(results, output_path)
    if not all_candidates:
        write_summary_tables(results, output_path)

    return output_path


def copy_config(dirpath: str | Path) -> Path:
    """Copy the current configuration file to the specified directory.

    Args:
        dirpath: Path to the directory to copy the configuration file to.

    Returns:
        Path to the copied configuration file.
    """
    filepath = Path(dirpath) / "config.yaml"
    from_ = open(utils.get_config_path(), "r", encoding="utf8")
    to_ = open(filepath, "w", encoding="utf8")
    with from_, to_:
        to_.write(from_.read())
    return filepath


def update_config(filepath: str | Path) -> None:
    """Update the configuration file.

    Args:
        filepath: Path to the new configuration file.

    Raises:
        ConfigError: When the new configuration is invalid.
    """
    # First, check the validity of the new configuration
    new_config = Config.from_yaml(filepath)
    new_config.validate()
    # If valid, overwrite the default configuration
    from_ = open(filepath, "r", encoding="utf8")
    to_ = open(utils.get_config_path(), "w", encoding="utf8")
    with from_, to_:
        to_.write(from_.read())


def copy_database(dirpath: str | Path) -> Path:
    """Copy the current database file to the specified directory.

    Args:
        dirpath: Path to the directory to copy the database file to.

    Returns:
        Path to the copied database file.
    """
    filepath = Path(dirpath) / "database.byonic"
    from_ = open(utils.get_db_path(), "r", encoding="utf8")
    to_ = open(filepath, "w", encoding="utf8")
    with from_, to_:
        to_.write(from_.read())
    return filepath


def update_database(filepath: str | Path) -> None:
    """Update the database file."""
    # First, check the validity of the new database
    try:
        Database.from_byonic(filepath)
    except Exception as e:
        raise DatabaseError(f"Invalid database file: {e}.\nConsult Fu Bin for help.")
    # If valid, overwrite the default database
    from_ = open(filepath, "r", encoding="utf8")
    to_ = open(utils.get_db_path(), "w", encoding="utf8")
    with from_, to_:
        to_.write(from_.read())
