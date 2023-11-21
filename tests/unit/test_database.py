import pytest

import glyhunter.database


@pytest.fixture(autouse=True)
def simple_masses(monkeypatch):
    monkeypatch.setattr(
        glyhunter.database, "MASSES", {"A": 1.0, "B": 2.0, "C": 3.0, "Na+": 1.0, "H20": 10}
    )


@pytest.fixture(autouse=True)
def simple_monosaccharides(monkeypatch):
    monkeypatch.setattr(glyhunter.database, "MONOSACCHARIDES", ["A", "B", "C"])


class TestMonoSaccharide:
    def test_validate_name(self):
        with pytest.raises(ValueError):
            glyhunter.database.MonoSaccharide(name="D")

    def test_str(self):
        assert str(glyhunter.database.MonoSaccharide(name="A")) == "A"
        assert (
            str(glyhunter.database.MonoSaccharide(name="A", modi=1.0)) == "A[+1.0000]"
        )

    def test_mass(self):
        assert glyhunter.database.MonoSaccharide(name="A").mass == 1.0
        assert glyhunter.database.MonoSaccharide(name="A", modi=1.0).mass == 2.0


class TestComposition:
    @pytest.fixture
    def mono_1(self):
        return glyhunter.database.MonoSaccharide(name="A")

    @pytest.fixture
    def mono_2(self):
        return glyhunter.database.MonoSaccharide(name="B", modi=1.0)

    def test_str(self, mono_1, mono_2):
        comp = glyhunter.database.Composition(comp={mono_1: 1, mono_2: 2})
        assert str(comp) == "A(1)B[+1.0000](2)"

    def test_order(self, mono_1, mono_2):
        # The order of the monosaccharides should be sorted by their name
        # according to the order of MONOSACCHARIDES
        comp = glyhunter.database.Composition(comp={mono_2: 1, mono_1: 2})
        assert str(comp) == "A(2)B[+1.0000](1)"

    def test_mass(self, mono_1, mono_2):
        comp = glyhunter.database.Composition(comp={mono_1: 1, mono_2: 2})
        assert comp.mass == 17.0

    def test_reducing_end(self, mono_1, mono_2):
        comp = glyhunter.database.Composition(
            comp={mono_1: 1, mono_2: 2}, reducing_end=1.0
        )
        assert comp.mass == 18.0


class TestIon:
    @pytest.fixture
    def mono_1(self):
        return glyhunter.database.MonoSaccharide(name="A")

    @pytest.fixture
    def mono_2(self):
        return glyhunter.database.MonoSaccharide(name="B", modi=1.0)

    @pytest.mark.parametrize(
        "charge, mz",
        [
            (1, 18.0),
            (2, 9.5),
        ],
    )
    def test_mz(self, mono_1, mono_2, charge, mz):
        result = glyhunter.database.Ion(
            comp=glyhunter.database.Composition(comp={mono_1: 1, mono_2: 2}),
            charge=charge,
            charge_carrier="Na+",
        )
        assert result.mz == mz


class TestDatabase:
    def test_from_byonic_basic(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("A(1)B(2) % 100.0\nA(2) % 50.0")

        # Build the database
        db = glyhunter.database.Database.from_byonic(
            byonic_file, charge_carrier="H+", charges=[1], modifications=None
        )

        # Check the database
        assert len(db.data) == 2
        assert str(db.data[0].comp) == "A(1)B(2)"
        assert db.data[0].charge == 1
        assert db.data[0].charge_carrier == "H+"
        assert str(db.data[1].comp) == "A(2)"
        assert db.data[1].charge == 1
        assert db.data[1].charge_carrier == "H+"

    def test_from_byonic_blank_lines(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("\nA(1)B(2) % 100.0\n\n")

        # Build the database
        db = glyhunter.database.Database.from_byonic(byonic_file)

        # Check the database
        assert len(db.data) == 1
        assert str(db.data[0].comp) == "A(1)B(2)"

    def test_from_byonic_one_modification(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("A(1)B(2) % 100.0")

        # Build the database
        db = glyhunter.database.Database.from_byonic(
            byonic_file, charge_carrier="Na+", charges=[1], modifications={"A": [1.0]}
        )

        # Check the database
        assert len(db.data) == 1
        assert str(db.data[0].comp) == "A[+1.0000](1)B(2)"

    def test_from_byonic_two_modifications_for_one_monosaccharide(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("A(1)B(2) % 100.0")

        # Build the database
        db = glyhunter.database.Database.from_byonic(
            byonic_file,
            charge_carrier="Na+",
            charges=[1],
            modifications={"A": [1.0, 2.0]},
        )

        # Check the database
        assert len(db.data) == 2
        assert str(db.data[0].comp) == "A[+1.0000](1)B(2)"
        assert str(db.data[1].comp) == "A[+2.0000](1)B(2)"

    def test_from_byonic_modifications_for_two_monosaccharide(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("A(1)B(2) % 100.0")

        # Build the database
        db = glyhunter.database.Database.from_byonic(
            byonic_file,
            charge_carrier="Na+",
            charges=[1],
            modifications={"A": [0.0, 1.0], "B": [2.0]},
        )

        # Check the database
        assert len(db.data) == 2
        assert str(db.data[0].comp) == "A(1)B[+2.0000](2)"
        assert str(db.data[1].comp) == "A[+1.0000](1)B[+2.0000](2)"

    def test_from_byonic_reducing_end(self, tmp_path):
        # Make a byonic file in the temp dir
        byonic_file = tmp_path / "glycans.byonic"
        byonic_file.write_text("A(1)B(2) % 100.0")

        # Build the database
        db = glyhunter.database.Database.from_byonic(byonic_file, reducing_end=1.0)

        # Check the database
        assert len(db.data) == 1
        assert str(db.data[0].comp) == "A(1)B(2)"
        assert db.data[0].comp.reducing_end == 1.0

    @pytest.fixture
    def db_for_search(self, tmp_path):
        """Build a database for search testing."""
        ions = [f"A({i})" for i in range(1, 6)]
        byonic_file = tmp_path / "glycans.byonic"
        text = "\n".join(f"{ion} % 100.0" for ion in ions)  # 100.0 is dummy value
        byonic_file.write_text(text)
        db = glyhunter.database.Database.from_byonic(byonic_file)
        return db

    def test_search(self, db_for_search):
        result = db_for_search.search(13.0, 0.1)
        assert len(result) == 1
        assert str(result[0].comp) == "A(2)"

    def test_search_many_results(self, db_for_search):
        # Note that in this case, the result is sorted by the difference between
        # the m/z and the given m/z.
        result = db_for_search.search(12.9, 1.5)
        assert len(result) == 3
        assert [str(r.comp) for r in result] == ["A(2)", "A(1)", "A(3)"]

    def test_search_no_result(self, db_for_search):
        result = db_for_search.search(20.0, 0.1)
        assert len(result) == 0

    def test_search_closest(self, db_for_search):
        result = db_for_search.search_closest(13.0, 0.1)
        assert str(result.comp) == "A(2)"

    def test_search_closest_no_result(self, db_for_search):
        result = db_for_search.search_closest(20.0, 0.1)
        assert result is None
