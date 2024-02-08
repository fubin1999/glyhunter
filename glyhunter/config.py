from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar, Optional

import yaml
from attrs import define, field

__all__ = [
    "Config",
    "load_config",
    "ConfigError",
    "ConfigKeyError",
    "ConfigValueError",
    "ConfigTypeError",
]


def load_config(filepath: Optional[str | Path] = None) -> Config:
    """Load a config from a given file or the default file.

    If config is built from a given config file, it will be validated
    before returned.

    Args:
        filepath: Path to the config file. If None (default),
            load the default config file from the .glyhunter directory.

    Returns:
        Config: The config object.

    Raises:
        ConfigError: When the config is invalid.
    """
    if filepath is None:
        config = Config.default()
    else:
        config = Config.from_yaml(filepath)
        config.validate()
    return config


class ConfigError(Exception):
    """Base class for all exceptions raised by Config."""


class ConfigKeyError(ConfigError, KeyError):
    """Raised when a key is not found in Config."""


class ConfigValueError(ConfigError, ValueError):
    """Raised when a value is invalid in Config."""


class ConfigTypeError(ConfigError, TypeError):
    """Raised when a value has an invalid type in Config."""


@define
class Config:
    """Manager of all configurations."""

    validators: ClassVar[list[Callable[[dict[str, Any]], None]]] = []

    _data: dict[str, Any] = field(factory=dict, converter=dict)

    @classmethod
    def from_yaml(cls, filepath: str | Path) -> Config:
        """Load a config from a yaml file."""
        data = yaml.safe_load(open(filepath, encoding="utf-8"))
        return cls(data)

    @classmethod
    def default(cls) -> Config:
        """Return the default config."""
        default_path = Path.home() / ".glyhunter" / "config.yaml"
        return cls.from_yaml(default_path)

    def validate(self):
        """Validate the config."""
        for validator in self.validators:
            validator(self._data)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def items(self) -> list[tuple[str, Any]]:
        return list(self._data.items())

    def to_dict(self) -> dict[str, Any]:
        return self._data.copy()


def register_validator(validator: Callable[[dict[str, Any]], None]) -> None:
    """Register a validator for Config."""
    Config.validators.append(validator)


def validate_exist(data: dict[str, Any], key: str) -> None:
    """Validate if a key exists."""
    if key not in data:
        raise ConfigKeyError(f"'{key}' is required.")


@register_validator
def validate_mz_tol(data: dict[str, Any]) -> None:
    """Validate mz_tol."""
    validate_exist(data, "mz_tol")
    mz_tol = data["mz_tol"]
    if not isinstance(mz_tol, (float, int)):
        raise ConfigTypeError(f"'mz_tol' must be a float, not {type(mz_tol)}.")
    if mz_tol <= 0:
        raise ConfigValueError(f"'mz_tol' must be positive, not {mz_tol}.")
    if mz_tol > 100:
        raise ConfigValueError(f"'mz_tol' must be less than 100, not {mz_tol}.")


@register_validator
def validate_modifications(data: dict[str, Any]) -> None:
    """Validate modifications."""
    monos = ["Hex", "HexNAc", "dHex", "Pen", "NeuAc", "NeuGc", "KDN", "HexA"]

    match data.get("modifications"):
        case None:
            raise KeyError("Missing key 'modifications'")
        case dict(modifications) if not all(
            isinstance(k, str) and isinstance(v, list) for k, v in modifications.items()
        ):
            raise ConfigTypeError("'modifications' must be a dict of lists.")
        case dict(modifications):
            # Check if all monosaccharides in modifications are valid
            not_valid = set(modifications.keys()) - set(monos)
            if not_valid:
                raise ConfigValueError(
                    f"Unknown monosaccharides in 'modifications': {not_valid}."
                )

            # Check if any monosaccharide is missing
            missing = set(monos) - set(modifications.keys())
            if missing:
                raise ConfigValueError(
                    f"Missing monosaccharides in 'modifications': {missing}."
                )

            # Check if the format of the modifications is correct.
            # That is, every value is a list of floats.
            for key, value in modifications.items():
                for v in value:
                    if not isinstance(v, (float, int)):
                        raise ConfigTypeError(
                            f"The value of '{key}' must be a list of floats, not {type(v)}."
                        )
        case _:
            raise ConfigTypeError(f"'modifications' must be a dict.")


@register_validator
def validate_reducing_end(data: dict[str, Any]) -> None:
    """Validate reducing_end."""
    validate_exist(data, "reducing_end")
    reducing_end = data["reducing_end"]
    if not isinstance(reducing_end, (float, int)):
        raise ConfigTypeError(
            f"'reducing_end' must be a float, not {type(reducing_end)}."
        )
    if reducing_end < 0:
        raise ConfigValueError(
            f"'reducing_end' must be non-negative, not {reducing_end}."
        )


@register_validator
def validate_charge_carrier(data: dict[str, Any]) -> None:
    """Validate charge_carrier."""
    validate_exist(data, "charge_carrier")
    charge_carrier = data["charge_carrier"]
    if not isinstance(charge_carrier, str):
        raise ConfigTypeError(
            f"'charge_carrier' must be a string, not {type(charge_carrier)}."
        )
    if charge_carrier not in ["H+", "Na+", "K+"]:
        raise ConfigValueError(
            f"'charge_carrier' must be 'H+', 'Na+' or 'K+', not {charge_carrier}."
        )


@register_validator
def validate_calibration_on(data: dict[str, Any]) -> None:
    """Validate calibration_on."""
    validate_exist(data, "calibration_on")
    calibration_on = data["calibration_on"]
    if not isinstance(calibration_on, bool):
        raise ConfigTypeError(
            f"'calibration_on' must be a boolean, not {type(calibration_on)}."
        )


@register_validator
def validate_calibration_by(data: dict[str, Any]) -> None:
    """Validate calibration_by."""
    validate_exist(data, "calibration_by")
    calibration_by = data["calibration_by"]
    if not isinstance(calibration_by, list):
        raise ConfigTypeError(
            f"'calibration_by' must be a list, not {type(calibration_by)}."
        )
    if not all(isinstance(x, (float, int)) for x in calibration_by):
        raise ConfigTypeError(
            f"'calibration_by' must be a list of floats, not {calibration_by}."
        )
    if len(calibration_by) < 2:
        raise ConfigValueError(
            f"'calibration_by' must have at least 2 values, "
            f"not {len(calibration_by)}."
        )


@register_validator
def validate_calibration_tol(data: dict[str, Any]) -> None:
    """Validate calibration_tol."""
    validate_exist(data, "calibration_tol")
    calibration_tol = data["calibration_tol"]
    if not isinstance(calibration_tol, (float, int)):
        raise ConfigTypeError(
            f"'calibration_tol' must be a float, not {type(calibration_tol)}."
        )
    if calibration_tol <= 0:
        raise ConfigValueError(
            f"'calibration_tol' must be positive, not {calibration_tol}."
        )
    if calibration_tol > 500:
        raise ConfigValueError(
            f"'calibration_tol' must be less than 500, not {calibration_tol}."
        )


@register_validator
def valid_constraints(data: dict[str, Any]) -> None:
    """Validate constraints."""
    validate_exist(data, "constraints")
    constraints = data["constraints"]
    if not isinstance(constraints, dict):
        raise ConfigTypeError(f"'constraints' must be a dict, not {type(constraints)}.")
    if not all(
        isinstance(k, str) and isinstance(v, list) for k, v in constraints.items()
    ):
        raise ConfigTypeError("'constraints' must be a dict of lists.")
    for key, (min_, max_) in constraints.items():
        if not isinstance(min_, int):
            raise ConfigTypeError(
                f"The minimum value of '{key}' must be an integer, not {type(min_)}."
            )
        if not isinstance(max_, int):
            raise ConfigTypeError(
                f"The maximum value of '{key}' must be an integer, not {type(max_)}."
            )
        if max_ < min_:
            raise ConfigValueError(
                f"The maximum value of '{key}' must be greater than "
                f"the minimum value, not {min_} > {max_}."
            )
        if min_ < 0:
            raise ConfigValueError(
                f"The minimum value of '{key}' must be non-negative, not {min_}."
            )


@register_validator
def valid_global_mod_constraints(data: dict[str, Any]) -> None:
    """Validate global_modification_constraints."""
    validate_exist(data, "global_modification_constraints")
    value: dict[str, int] = data["global_modification_constraints"]
    if set(value) != {"Ac", "P", "S"}:
        raise ConfigValueError(
            "Please do not change the keys of `global_modification_constraints`. "
            "The keys must be exactly 'Ac', 'P' and 'S'."
        )
    for key, max_ in value.items():
        if not isinstance(max_, int):
            raise ConfigTypeError(
                f"The maximum value of '{key}' must be an integer, not {type(max_)}."
            )
        if max_ < 0:
            raise ConfigValueError(
                f"The maximum value of '{key}' must be non-negative, not {max_}."
            )
