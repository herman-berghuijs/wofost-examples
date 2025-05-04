from configs.config_02 import crop, cultivar, lat, lon, CO2, NH4I, NO3I, WAV
from configs.config_02 import agro_fp, fig_fp, output_fp, weather_fp
from libs.SoilGridsDataProvider import SoilGridsDataProvider
import matplotlib.pyplot as plt
import pandas as pd
from pcse.base import ParameterProvider
from pcse.input import ExcelWeatherDataProvider, WOFOST81SiteDataProvider_SNOMIN, YAMLCropDataProvider
from pcse.models import Wofost81_NWLP_MLWB_SNOMIN
import yaml

def main():
    agrod = yaml.safe_load(open(agro_fp))
    cropd = YAMLCropDataProvider(Wofost81_NWLP_MLWB_SNOMIN)

    sdp = SoilGridsDataProvider(lat, lon, 120.)
    soild = sdp.soil_yaml

    nlayer = len(sdp.soil_yaml["SoilProfileDescription"]["SoilLayers"])
    NH4Ilist = [0] * nlayer
    NO3Ilist = [0] * nlayer
    NH4Ilist[0] = NH4I
    NO3Ilist[0] = NO3I
    sited = WOFOST81SiteDataProvider_SNOMIN(CO2 = CO2, NH4I = NH4Ilist, NO3I = NO3Ilist, WAV = WAV)

    wdp = ExcelWeatherDataProvider(weather_fp)

    # Build model and run it
    parameters = ParameterProvider(sitedata=sited, soildata=soild, cropdata=cropd)
    model = Wofost81_NWLP_MLWB_SNOMIN(parameters, wdp, agrod)
    model.run_till_terminate()

    # Collect simulation output
    df = pd.DataFrame(model.get_output()).set_index("day")
    fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(16, 8))
    df["LAI"].plot(ax=axs[0], label="LAI", color='k')
    df["WST"].plot(ax=axs[1], label="Stems")
    df["WLVG"].plot(ax=axs[1], label="Green leaves")
    df["WSO"].plot(ax=axs[1], label="Tubers")
    axs[0].set_title("Leaf Area Index")
    axs[1].set_title("Crop biomass")
    r = axs[1].legend()
    fig.autofmt_xdate()

    # Save output
    fig.savefig(fig_fp, dpi=600)
    df.to_excel(output_fp)

    print(soild)

if __name__ == "__main__":
    main()