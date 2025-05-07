from pathlib import Path

lat = 52.01
lon = 5.3

# Set url
url_bofek2020 = "https://www.wur.nl/nl/show/bofek-2020-gis-1.htm"

# Set paths
cwd = Path.cwd()
input_dir = cwd / "input" / "03"
output_dir = cwd / "output" / "03"
bofek_dir = input_dir / "BOFEK2020"
bofek_zip2_fp = bofek_dir / "BOFEK2020_GIS.7z"
bofek_shape_fp = bofek_dir / "GIS" / "shp_files" / "bod_clusters.shp"
staring_series_dir = input_dir / "StaringSeries"
profile_info_fp = staring_series_dir / "profile_info.csv"
staring_series_fp = staring_series_dir / "StaringReeksPARS_2018.csv"
all_profiles_fp = staring_series_dir / "AllProfiles_368.csv"
soilcode_fp = staring_series_dir / "BodemCode.csv"

