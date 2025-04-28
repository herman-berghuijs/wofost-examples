from pathlib import Path

# Input parameters
crop = "potato"
cultivar = "Fontane"

# Set paths
cwd = Path.cwd()
input_dir = cwd / "input" / "01"
output_dir = cwd / "output" / "01"
agro_dir = input_dir / "agro"
agro_fp = agro_dir / "01_agro.yaml"
site_dir = input_dir / "site"
site_fp = site_dir / "01_site.yaml"
soil_dir = input_dir / "soil"
soil_fp = soil_dir / "01_soil.yaml"
weather_dir = input_dir / "weather"
weather_fp = weather_dir / "01_weather.csv"
output_fp = output_dir / "output.xlsx"
fig_fp = output_dir / "timeplots.jpeg"