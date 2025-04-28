# Import required packages
from pcse.base import ParameterProvider
from pcse.input import CSVWeatherDataProvider, YAMLCropDataProvider
from pcse.models import Wofost72_PP
import matplotlib.pyplot as plt
from configs.config_01 import agro_fp, crop, cultivar, fig_fp, output_fp, site_fp, soil_fp, weather_fp
import pandas as pd
import yaml

def main():
    # Load model input data
    agrod = yaml.safe_load(open(agro_fp))
    cropd = YAMLCropDataProvider(Wofost72_PP)
    sited = yaml.safe_load(open(site_fp))
    soild = yaml.safe_load(open(soil_fp))
    wdp = CSVWeatherDataProvider(weather_fp)

    # Build model and run it
    parameters = ParameterProvider(sitedata=sited, soildata=soild, cropdata=cropd)
    model = Wofost72_PP(parameters, wdp, agrod)
    model.run_till_terminate()

    # Collect simulation output
    df = pd.DataFrame(model.get_output()).set_index("day")
    fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(16, 8))
    df["LAI"].plot(ax=axs[0], label="LAI", color='k')
    df["TAGP"].plot(ax=axs[1], label="Total biomass")
    df["TWSO"].plot(ax=axs[1], label="Yield")
    axs[0].set_title("Leaf Area Index")
    axs[1].set_title("Crop biomass")
    r = axs[1].legend()
    fig.autofmt_xdate()

    # Save output
    fig.savefig(fig_fp, dpi=600)
    df.to_excel(output_fp)


if __name__ == "__main__":
    main()
