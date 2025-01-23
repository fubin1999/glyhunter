import importlib.resources as res
import tempfile
from pathlib import Path
import zipfile

import streamlit as st

import glyhunter as gh


@st.cache_data
def load_default_config():
    config_res_path = res.files("glyhunter").joinpath("resources/config.yaml")
    return config_res_path.read_text(encoding="utf8")


@st.cache_data
def load_default_db():
    db_res_path = res.files("glyhunter").joinpath("resources/database.byonic")
    return db_res_path.read_text(encoding="utf8")


st.title("GlyHunter")
st.write("GlyHunter is a tool for glycan annotation from flexAnalysis exported data.")

st.header("Input Files")

# Upload the XLSX data file.
data_file = st.file_uploader(
    "Upload an XLSX data exported from flexAnalysis.", type=["xlsx"]
)
with st.expander("File description"):
    st.write("In flexAnalysis, select `File` - `Export` - `Export to Excel`.")
    st.write("Each sheet in the XLSX file should be a spectrum.")

# Upload the configuration file.
config_file = st.file_uploader(
    "Upload a configuration file. (Or use default)", type=["yaml"]
)
with st.expander("File description"):
    st.info(
        "Leave this field empty to use the default configuration, "
        "which only works for human serum N-glycans with methylamide derivatization."
    )
    st.write(
        "The configuration file is a YAML file that specifies the parameters for GlyHunter. "
        "Click the button below to download the configuration file template. "
        "Detailed instructions can be found in the template."
    )
    st.download_button(
        label="Download the configuration file template",
        data=load_default_config(),
        file_name="config.yaml",
        mime="text/yaml",
    )

# Upload the database file.
database_file = st.file_uploader(
    "Upload a database file. (Or use default)", type=["byonic"]
)
with st.expander("File description"):
    st.info("Leave this field empty to use the default human N-glycan database.")
    st.write(
        "The database file is a text file that contains the glycan database for GlyHunter. "
        "Click the button below to download the default database file for reference. "
        "The file is in Byonic format, and can by opened by any text editor. "
        "Glycan database downloaded directly from Byonic can be used. "
        "Or, manually create a text file with '.byonic' suffix in the same way as the default "
        "database file. "
    )
    st.write(
        "**The masses of glycans in the database file will be ignored by GlyHunter, "
        "so if you are preparing a database file manually, "
        "just put in random numbers.**"
    )
    st.download_button(
        label="Download the database file template",
        data=load_default_db(),
        file_name="database.byonic",
        mime="text/byonic",
    )

# Run GlyHunter.
if data_file is None:
    st.stop()

st.header("Run GlyHunter")

if st.button("Run"):
    with tempfile.TemporaryDirectory() as tempdir:
        data_file_path = Path(tempdir) / "data.xlsx"
        data_file_path.write_bytes(data_file.getvalue())
        config_file_path = Path(tempdir) / "config.yaml"
        if config_file:
            config_file_path.write_bytes(config_file.getvalue())
        else:
            config_file_path.write_text(load_default_config(), encoding="utf8")
        database_file_path = Path(tempdir) / "database.byonic"
        if database_file:
            database_file_path.write_bytes(database_file.getvalue())
        else:
            database_file_path.write_text(load_default_db(), encoding="utf8")
        output_path = Path(tempdir) / "output"
        gh.run(data_file_path, output_path, config_file_path, database_file_path)
        # compress the output directory
        zip_filepath = Path(tempdir) / "glyhunter_results.zip"
        with zipfile.ZipFile(zip_filepath, mode="w") as archive:
            for file in output_path.rglob("*"):
                archive.write(file, file.relative_to(output_path))
        st.success(f"Done!")
        st.download_button(
            label="Download the results",
            data=zip_filepath.read_bytes(),
            file_name="glyhunter_results.zip",
            mime="application/zip",
        )
