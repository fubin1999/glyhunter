import pytest

from glyhunter import utils


def test_output_directory(clean_dir):
    input_filepath = clean_dir / "somefile.xlsx"
    result = utils.output_directory(input_filepath)
    assert result == clean_dir / "somefile_glyhunter_results"
