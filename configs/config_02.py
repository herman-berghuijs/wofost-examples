from pathlib import Path

# Input parameters
crop = "potato"
cultivar = "Fontane"

# Set paths
cwd = Path.cwd()
input_dir = cwd / "input" / "02"
output_dir = cwd / "output" / "02"
agro_dir = input_dir / "agro"
agro_fp = agro_dir / "02_agro.yaml"
weather_dir = input_dir / "weather"
weather_fp = weather_dir / "02_weather.xlsx"
output_fp = output_dir / "output.xlsx"
fig_fp = output_dir / "timeplots.jpeg"

CO2 = 400.
NH4I = 5.
NO3I = 25.
WAV = 10.
lat = 52.01
lon = 5.3