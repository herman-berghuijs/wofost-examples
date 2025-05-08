from configs.config_03 import (all_profiles_fp, soilcode_fp, bofek_dir, bofek_zip2_fp, bofek_shape_fp,
                               staring_series_dir, staring_series_fp, url_bofek2020)
from configs.config_03 import agro_fp, fig_fp, output_fp, weather_fp
from configs.config_03 import CO2, lat, lon, WAV
from libs.util import Util
import geopandas as gpd
import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import py7zr
import requests
import zipfile
from shapely import Point, Polygon
from types import SimpleNamespace
import yaml
from pcse.base import ParameterProvider
from pcse.input import ExcelWeatherDataProvider, WOFOST81SiteDataProvider_SNOMIN, YAMLCropDataProvider
from pcse.models import Wofost81_WLP_MLWB
from libs.BOFEK2020DataProvider import BOFEK2020DataProvider

def main():
    agrod = yaml.safe_load(open(agro_fp))
    cropd = YAMLCropDataProvider(Wofost81_WLP_MLWB)
    bd = BOFEK2020DataProvider(lat, lon, bofek_dir, staring_series_dir, 125.)
    soild = bd.soil_yaml
    nlayer = len(bd.soil_yaml["SoilProfileDescription"]["SoilLayers"])
    NH4Ilist = [0] * nlayer
    NO3Ilist = [0] * nlayer
    NH4Ilist[0] = 100.
    NO3Ilist[0] = 100.
    sited = WOFOST81SiteDataProvider_SNOMIN(CO2 = CO2, NH4I = NH4Ilist, NO3I = NO3Ilist, WAV = WAV)
    wdp = ExcelWeatherDataProvider(weather_fp)
    parameters = ParameterProvider(sitedata=sited, soildata=soild, cropdata=cropd)
    model = Wofost81_WLP_MLWB(parameters, wdp, agrod)
    model.run_till_terminate()

    # Collect simulation output
    df = pd.DataFrame(model.get_output()).set_index("day")
    fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(16, 8))
    df["LAI"].plot(ax=axs[0], label="LAI", color='k')
    df["WLV"].plot(ax=axs[1], label="Leaf DM")
    df["WST"].plot(ax=axs[1], label="Stem DM")
    df["WSO"].plot(ax=axs[1], label="Yield")
    axs[0].set_title("Leaf Area Index")
    axs[1].set_title("Crop biomass")
    r = axs[1].legend()
    fig.autofmt_xdate()

    # Save output
    fig.savefig(fig_fp, dpi=600)
    df.to_excel(output_fp)

if __name__ == "__main__":
    main()

