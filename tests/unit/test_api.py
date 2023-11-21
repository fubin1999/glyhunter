import pytest

import glyhunter.utils
from glyhunter import api


class TestInitiate:

    def test_initiate_basic(self):
        """Test initiate() when no .glyhunter directory exists
        and force is False."""
        api.initiate()
        assert glyhunter.utils.get_glyhunter_dir().exists()
        assert glyhunter.utils.get_db_path().exists()
        assert glyhunter.utils.get_config_path().exists()

    def test_initiate_glyhunter_dir_exists(self):
        """Test initiate() when .glyhunter directory exists
        and force is False."""
        glyhunter.utils.get_glyhunter_dir().mkdir()
        with pytest.raises(FileExistsError) as e:
            api.initiate(force=False)
        assert "already exists" in str(e.value)

    def test_initiate_glyhunter_dir_exists_force(self):
        """Test initiate() when .glyhunter directory exists
        and force is True."""
        glyhunter.utils.get_glyhunter_dir().mkdir()
        glyhunter.utils.get_db_path().write_text("test_db")
        glyhunter.utils.get_config_path().write_text("test_config")

        api.initiate(force=True)

        assert glyhunter.utils.get_glyhunter_dir().exists()
        assert glyhunter.utils.get_db_path().exists()
        assert glyhunter.utils.get_config_path().exists()
        assert glyhunter.utils.get_db_path().read_text() != "test_db"
        assert glyhunter.utils.get_config_path().read_text() != "test_config"


@pytest.mark.usefixtures("glyhunter_init")
def test_copy_config(clean_dir):
    """Test copy_config()."""
    api.copy_config(clean_dir)
    assert (clean_dir / "config.yaml").exists()
    assert (clean_dir / "config.yaml").read_text() == glyhunter.utils.get_config_path().read_text()


@pytest.mark.usefixtures("glyhunter_init")
def test_update_config(clean_dir, mocker):
    """Test update_config()."""
    config_mock = mocker.Mock()
    config_mock.validate.return_value = True
    mocker.patch("glyhunter.api.Config.from_yaml", return_value=config_mock)

    new_config_file = clean_dir / "new_config.yaml"
    new_config_file.write_text("test")
    api.update_config(new_config_file)
    assert glyhunter.utils.get_config_path().exists()
    assert glyhunter.utils.get_config_path().read_text() == "test"


@pytest.mark.usefixtures("glyhunter_init")
def test_copy_database(clean_dir):
    """Test copy_database()."""
    api.copy_database(clean_dir)
    assert (clean_dir / "database.byonic").exists()
    assert (clean_dir / "database.byonic").read_text() == glyhunter.utils.get_db_path().read_text()


@pytest.mark.usefixtures("glyhunter_init")
def test_update_database(clean_dir, mocker):
    """Test update_database()."""
    mocker.patch("glyhunter.api.Config.from_yaml", return_value=mocker.Mock())
    new_db_file = clean_dir / "new_db.byonic"
    new_db_file.write_text("test")
    api.update_database(new_db_file)
    assert glyhunter.utils.get_db_path().exists()
    assert glyhunter.utils.get_db_path().read_text() == "test"


