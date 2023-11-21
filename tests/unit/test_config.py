import pytest

from glyhunter.config import Config, load_config


@pytest.fixture
def default_config():
    """Return a Config instance."""
    return Config.from_yaml("tests/data/test_config.yaml")


def test_load_config_with_file(mocker):
    config_mock = mocker.Mock()
    config_mock.validate = mocker.Mock()
    mocker.patch("glyhunter.config.Config.from_yaml", autospec=True, return_value=config_mock)
    result = load_config("tests/data/test_config.yaml")
    assert result == config_mock
    config_mock.validate.assert_called_once()


@pytest.mark.usefixtures("glyhunter_init")
def test_load_config_default(mocker):
    config_mock = mocker.Mock()
    mocker.patch("glyhunter.config.Config.default", autospec=True, return_value=config_mock)
    result = load_config()
    assert result == config_mock


def test_getitem(default_config):
    assert default_config["mz_tol"] == 50


def test_getitem_keyerror(default_config):
    with pytest.raises(KeyError):
        result = default_config["not_exist"]


def test_get(default_config):
    assert default_config.get("mz_tol") == 50


def test_get_default_value(default_config):
    assert default_config.get("not_exist", 100) == 100


def test_items(default_config):
    assert ("mz_tol", 50) in default_config.items()


def test_validate_mz_tol_not_exist(default_config):
    del default_config._data["mz_tol"]
    with pytest.raises(KeyError):
        default_config.validate()


def test_validate_mz_tol_not_int(default_config):
    default_config._data["mz_tol"] = "50"
    with pytest.raises(TypeError):
        default_config.validate()


def test_validate_mz_tol_too_large(default_config):
    default_config._data["mz_tol"] = 1000
    with pytest.raises(ValueError):
        default_config.validate()


def test_validate_mz_tol_too_small(default_config):
    default_config._data["mz_tol"] = 0
    with pytest.raises(ValueError):
        default_config.validate()


def test_validate_modifications_not_exist(default_config):
    del default_config._data["modifications"]
    with pytest.raises(KeyError):
        default_config.validate()


def test_validate_modifications_missing_mono(default_config):
    del default_config._data["modifications"]["Hex"]
    with pytest.raises(ValueError):
        default_config.validate()


def test_validate_modifications_wrong_format(default_config):
    # This test is for the case that a modification is not a list,
    # but a single float.
    # This can happen when the user deletes the "-" symble in the yaml file.
    default_config._data["modifications"]["Hex"] = 0.5
    with pytest.raises(TypeError):
        default_config.validate()


def test_validate_reducing_end_not_exist(default_config):
    del default_config._data["reducing_end"]
    with pytest.raises(KeyError):
        default_config.validate()


def test_validate_reducing_end_not_float(default_config):
    default_config._data["reducing_end"] = "0"
    with pytest.raises(TypeError):
        default_config.validate()


def test_validate_reducing_end_negative(default_config):
    default_config._data["reducing_end"] = -1
    with pytest.raises(ValueError):
        default_config.validate()


def test_validate_charge_carrier_not_exist(default_config):
    del default_config._data["charge_carrier"]
    with pytest.raises(KeyError):
        default_config.validate()


def test_validate_charge_carrier_not_str(default_config):
    default_config._data["charge_carrier"] = 0
    with pytest.raises(TypeError):
        default_config.validate()


def test_validate_charge_carrier_not_in_list(default_config):
    default_config._data["charge_carrier"] = "PO3+"
    with pytest.raises(ValueError):
        default_config.validate()


def test_validate_calibration_on_not_exist(default_config):
    del default_config._data["calibration_on"]
    with pytest.raises(KeyError):
        default_config.validate()


def test_validate_calibration_on_not_bool(default_config):
    default_config._data["calibration_on"] = 0
    with pytest.raises(TypeError):
        default_config.validate()


def test_validate_calibration_by_not_exist(default_config):
    del default_config._data["calibration_by"]
    with pytest.raises(KeyError):
        default_config.validate()


def test_validate_calibration_by_not_list(default_config):
    default_config._data["calibration_by"] = 0
    with pytest.raises(TypeError):
        default_config.validate()


def test_validate_calibration_by_not_float(default_config):
    default_config._data["calibration_by"] = ["0"]
    with pytest.raises(TypeError):
        default_config.validate()


def test_validate_calibration_by_too_short(default_config):
    default_config._data["calibration_by"] = [0]
    with pytest.raises(ValueError):
        default_config.validate()


def test_validate_calibration_tol_not_exist(default_config):
    del default_config._data["calibration_tol"]
    with pytest.raises(KeyError):
        default_config.validate()


def test_validate_calibration_tol_not_float(default_config):
    default_config._data["calibration_tol"] = "0"
    with pytest.raises(TypeError):
        default_config.validate()


def test_validate_calibration_tol_negative(default_config):
    default_config._data["calibration_tol"] = -1
    with pytest.raises(ValueError):
        default_config.validate()


def test_validate_calibration_tol_too_large(default_config):
    default_config._data["calibration_tol"] = 1000
    with pytest.raises(ValueError):
        default_config.validate()
