from pathlib import Path

crop = "wheat"
cultivar = "Winter_wheat_102"
lat = 52.01
lon = 5.3
CO2 = 400.
WAV = 10.

# Set url
url_bofek2020 = "https://www.wur.nl/nl/show/bofek-2020-gis-1.htm"

# Set paths
cwd = Path.cwd()
input_dir = cwd / "input" / "03"
agro_dir = input_dir / "agro"
agro_fp = agro_dir / "03_agro.yaml"
weather_dir = input_dir / "weather"
weather_fp = weather_dir / "03_weather.xlsx"
output_dir = cwd / "output" / "03"
output_fp = output_dir / "output.xlsx"
fig_fp = output_dir / "timeplots.jpeg"


bofek_dir = input_dir / "BOFEK2020"
bofek_zip2_fp = bofek_dir / "BOFEK2020_GIS.7z"
bofek_shape_fp = bofek_dir / "GIS" / "shp_files" / "bod_clusters.shp"
staring_series_dir = input_dir / "StaringSeries"
profile_info_fp = staring_series_dir / "profile_info.csv"
staring_series_fp = staring_series_dir / "StaringReeksPARS_2018.csv"
all_profiles_fp = staring_series_dir / "AllProfiles_368.csv"
soilcode_fp = staring_series_dir / "BodemCode.csv"

