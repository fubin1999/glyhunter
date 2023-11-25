import pytest

from glyhunter import database


class TestDatabase:
    def test_from_byonic_basic(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("A(1)B(2) % 100.0\nA(2) % 50.0")

        # Build the database
        db = database.Database.from_byonic(
            byonic_file, charge_carrier="H+", modifications=None
        )

        # Check the database
        assert len(db.data) == 2
        assert str(db.data[0]) == "A(1)B(2)"
        assert db.data[0].charge_carrier == "H+"
        assert str(db.data[1]) == "A(2)"
        assert db.data[1].charge_carrier == "H+"

    def test_from_byonic_blank_lines(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("\nA(1)B(2) % 100.0\n\n")

        # Build the database
        db = database.Database.from_byonic(byonic_file)

        # Check the database
        assert len(db.data) == 1
        assert str(db.data[0]) == "A(1)B(2)"

    def test_from_byonic_one_modification(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("A(1)B(2) % 100.0")

        # Build the database
        db = database.Database.from_byonic(
            byonic_file, charge_carrier="Na+", modifications={"A": [1.0]}
        )

        # Check the database
        assert len(db.data) == 1
        assert str(db.data[0]) == "A[+1.0000](1)B(2)"

    def test_from_byonic_two_modifications_for_one_monosaccharide(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("A(1)B(2) % 100.0")

        # Build the database
        db = database.Database.from_byonic(
            byonic_file,
            charge_carrier="Na+",
            modifications={"A": [1.0, 2.0]},
        )

        # Check the database
        assert len(db.data) == 2
        assert str(db.data[0]) == "A[+1.0000](1)B(2)"
        assert str(db.data[1]) == "A[+2.0000](1)B(2)"

    def test_from_byonic_modifications_for_two_monosaccharide(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("A(1)B(2) % 100.0")

        # Build the database
        db = database.Database.from_byonic(
            byonic_file,
            charge_carrier="Na+",
            modifications={"A": [0.0, 1.0], "B": [2.0]},
        )

        # Check the database
        assert len(db.data) == 2
        assert str(db.data[0]) == "A(1)B[+2.0000](2)"
        assert str(db.data[1]) == "A[+1.0000](1)B[+2.0000](2)"

    def test_from_byonic_global_modifications(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("A(1)B(2) % 100.0")

        # Build the database
        db = database.Database.from_byonic(
            byonic_file,
            charge_carrier="Na+",
            modifications={},
            global_mod_constraints={"Ac": 1},
        )

        # Check the database
        assert len(db.data) == 2
        assert set([str(ion) for ion in db.data]) == {"A(1)B(2)", "A(1)B(2)Ac(1)"}

    def test_from_byonic_both_modifications_and_global_modifications(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("A(1)B(2) % 100.0")

        # Build the database
        db = database.Database.from_byonic(
            byonic_file,
            charge_carrier="Na+",
            modifications={"A": [1.0, 0]},
            global_mod_constraints={"Ac": 1},
        )

        # Check the database
        assert len(db.data) == 4
        assert set([str(ion) for ion in db.data]) == {
            "A(1)B(2)",
            "A[+1.0000](1)B(2)",
            "A(1)B(2)Ac(1)",
            "A[+1.0000](1)B(2)Ac(1)",
        }

    def test_from_byonic_reducing_end(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("A(1)B(2) % 100.0")

        # Build the database
        db = database.Database.from_byonic(byonic_file, reducing_end=1.0)

        # Check the database
        assert len(db.data) == 1
        assert str(db.data[0]) == "A(1)B(2)"
        assert db.data[0].reducing_end == 1.0

    @pytest.fixture
    def db_for_search(self, tmp_path):
        """Build a database for search testing."""
        ions = [f"A({i})" for i in range(1, 6)]
        byonic_file = tmp_path / "glycans.byonic"
        text = "\n".join(f"{ion} % 100.0" for ion in ions)  # 100.0 is dummy value
        byonic_file.write_text(text)
        db = database.Database.from_byonic(byonic_file)
        return db

    def test_search(self, db_for_search):
        result = db_for_search.search(13.0, 0.1)
        assert len(result) == 1
        assert str(result[0]) == "A(2)"

    def test_search_many_results(self, db_for_search):
        # Note that in this case, the result is sorted by the difference between
        # the m/z and the given m/z.
        result = db_for_search.search(12.9, 1.5)
        assert len(result) == 3
        assert [str(r) for r in result] == ["A(2)", "A(1)", "A(3)"]

    def test_search_no_result(self, db_for_search):
        result = db_for_search.search(20.0, 0.1)
        assert len(result) == 0

    def test_search_closest(self, db_for_search):
        result = db_for_search.search_closest(13.0, 0.1)
        assert str(result) == "A(2)"

    def test_search_closest_no_result(self, db_for_search):
        result = db_for_search.search_closest(20.0, 0.1)
        assert result is None


class TestLoadDatabase:
    def test_load_with_file(self, mocker):
        mocker.patch(
            "glyhunter.database.Database.from_byonic", autospec=True, return_value="db"
        )
        db = database.load_database(
            "tests/data/glycans.byonic",
            charge_carrier="H+",
            reducing_end=1.0,
            modifications={},
            global_mod_constraints={},
        )
        assert db == "db"
        database.Database.from_byonic.assert_called_once_with(
            "tests/data/glycans.byonic",
            charge_carrier="H+",
            reducing_end=1.0,
            modifications={},
            global_mod_constraints={},
        )

    def test_load_without_file(self, mocker):
        mocker.patch(
            "glyhunter.database.Database.from_byonic", autospec=True, return_value="db"
        )
        mocker.patch("glyhunter.utils.get_db_path", autospec=True, return_value="path")
        db = database.load_database(
            None,
            charge_carrier="H+",
            reducing_end=1.0,
            modifications={},
            global_mod_constraints={},
        )
        assert db == "db"
        database.Database.from_byonic.assert_called_once_with(
            "path",
            charge_carrier="H+",
            reducing_end=1.0,
            modifications={},
            global_mod_constraints={},
        )
