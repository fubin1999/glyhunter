from pathlib import Path

import pandas as pd
import pytest

from glyhunter import results_export


def test_write_mass_list_results_with_valid_input(clean_dir):
    # Create a sample DataFrame
    df = pd.DataFrame({"glycan": ["G1", "G2"], "mass": [100.0, 200.0]})
    # Create a sample result
    results = [("mass_list_1", df)]
    # Call the function with the sample result and the temporary directory
    results_export.write_mass_list_results(results, clean_dir)
    # Check that the file was created and has the expected content
    expected_file = Path(clean_dir) / "mass_list_1.csv"
    assert expected_file.exists()
    result_df = pd.read_csv(expected_file)
    pd.testing.assert_frame_equal(result_df, df)


def test_write_mass_list_results_with_empty_input(clean_dir):
    # Call the function with an empty list and the temporary directory
    results_export.write_mass_list_results([], clean_dir)
    # Check that no file was created
    assert len(list(Path(clean_dir).iterdir())) == 0


@pytest.mark.parametrize(
    "by, expected_df",
    [
        (
            "intensity",
            pd.DataFrame(
                {
                    "mass_list_1": [100.0, 200.0, None],
                    "mass_list_2": [700.0, None, 800.0],
                },
                index=pd.Series(["G1", "G2", "G3"], name="glycan"),
            ),
        ),
        (
            "area",
            pd.DataFrame(
                {
                    "mass_list_1": [300.0, 400.0, None],
                    "mass_list_2": [900.0, None, 1000.0],
                },
                index=pd.Series(["G1", "G2", "G3"], name="glycan"),
            ),
        ),
        (
            "sn",
            pd.DataFrame(
                {
                    "mass_list_1": [500.0, 600.0, None],
                    "mass_list_2": [1100.0, None, 1200.0],
                },
                index=pd.Series(["G1", "G2", "G3"], name="glycan"),
            ),
        ),
    ],
)
def test_write_summary_tables_with_valid_input(clean_dir, by, expected_df):
    df1 = pd.DataFrame(
        {
            "glycan": ["G1", "G2"],
            "intensity": [100.0, 200.0],
            "area": [300.0, 400.0],
            "sn": [500.0, 600.0],
        }
    )
    df2 = pd.DataFrame(
        {
            "glycan": ["G1", "G3"],
            "intensity": [700.0, 800.0],
            "area": [900.0, 1000.0],
            "sn": [1100.0, 1200.0],
        }
    )
    results = [("mass_list_1", df1), ("mass_list_2", df2)]
    results_export.write_summary_tables(results, clean_dir)
    expected_file = Path(clean_dir) / f"summary_{by}.csv"
    assert expected_file.exists()
    result_df = pd.read_csv(expected_file, index_col="glycan")
    pd.testing.assert_frame_equal(result_df, expected_df)
