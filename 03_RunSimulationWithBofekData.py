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
#
# def get_bofek2020_data():
#     if bofek_shape_fp.exists():
#         pass
#     else:
#         response = requests.get(url_bofek2020)
#         content = response.content
#         response.close()
#         z = zipfile.ZipFile(io.BytesIO(content))
#         z.extractall(bofek_dir)
#         z.close()
#         s = py7zr.SevenZipFile(bofek_zip2_fp, 'r')
#         s.extractall(bofek_dir)
#         s.close()
#     gdf_bofek = gpd.read_file(bofek_shape_fp)
#     gdf_bofek = gdf_bofek.to_crs("EPSG:4326")
#     return gdf_bofek
#
# def get_soilcode(gdf_bofek, lat, lon):
#     min_lat = lat - 0.001
#     max_lat = lat + 0.001
#     min_lon = lon - 0.001
#     max_lon =  lon + 0.001
#     gdf_bofek = gdf_bofek.clip([min_lon, min_lat, max_lon, max_lat])
#
#     cond = gdf_bofek.contains(Point(lon, lat))
#     soilcode = gdf_bofek[cond].BODEMCODE.iloc[0]
#     return soilcode
#
# def get_soilid(soilcode):
#     df_soilcode = pd.read_csv(soilcode_fp)
#     cond = df_soilcode.BodemCode == soilcode
#     soilid = df_soilcode[cond].iProfile.iloc[0]
#     return soilid
#
# def get_staring_blocks_profile(soilid):
#     df_profiles = pd.read_csv(all_profiles_fp)
#     df_profile = df_profiles[df_profiles.iProfile == soilid]
#     df_profile = df_profile.replace(99999, np.nan)
#     df_profile = df_profile.replace(0, np.nan)
#     df_profile = df_profile.dropna(axis = 1)
#     nlayer = int(df_profile.columns[-1][-1])
#     soil_profile = SimpleNamespace(iProfile = [],
#                                    layerid = [],
#                                    minimum_depth = [],
#                                    maximum_depth = [],
#                                    thickness = [],
#                                    isoil = [],
#                                    staring_block = [])
#     minimum_depth = 0
#     for layerid in range(1,nlayer+1):
#         maximum_depth = df_profile[f"iZ{layerid}"].iloc[0]
#         thickness = maximum_depth - minimum_depth
#         isoil = df_profile[f"iSoil{layerid}"].iloc[0]
#         staring_block = get_staring_block(isoil)
#         soil_profile.iProfile.append(soilid)
#         soil_profile.layerid.append(layerid)
#         soil_profile.minimum_depth.append(minimum_depth)
#         soil_profile.maximum_depth.append(maximum_depth)
#         soil_profile.thickness.append(thickness)
#         soil_profile.isoil.append(isoil)
#         soil_profile.staring_block.append(staring_block)
#         minimum_depth = maximum_depth
#     df_staring_blocks = pd.DataFrame.from_dict(vars(soil_profile))
#     return df_staring_blocks
#
# def get_staring_block(isoil):
#     ntopsoils = 18
#     if isoil <= ntopsoils:
#         staring_block = f"B{str(isoil).zfill(1)}"
#     else:
#         staring_block = f"O{str(isoil - ntopsoils).zfill(1)}"
#     return staring_block
#
# def get_vangenuchten_profile(df_staring_blocks):
#     df_vgn_profiles = pd.read_csv(staring_series_fp)
#     df_vgn_profile = pd.merge(how = 'left',
#                               left = df_staring_blocks,
#                               right = df_vgn_profiles,
#                               left_on = ["staring_block"],
#                               right_on = ["Name"])
#     return df_vgn_profile

if __name__ == "__main__":
    main()

