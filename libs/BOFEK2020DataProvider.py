from types import SimpleNamespace
from libs.util import Util
from libs.water_retention_curves import VanGenuchten
from geopandas import gpd
from pathlib import Path
import inspect
import io
import numpy as np
import pandas as pd
from shapely import Point
import py7zr
import requests
import yaml
import zipfile

class BOFEK2020DataProvider():
    url_bofek2020 = "https://www.wur.nl/nl/show/bofek-2020-gis-1.htm"
    PFFieldCapacity = 2.0
    PFWiltingPoint = 4.2
    pFs = [-1.0, 1.0, 1.3, 1.7, 2.0, 2.3, 2.4, 2.7, 3.0, 3.3, 3.7, 4.0, 4.2, 6.0]
    SurfaceConductivity = 70.

    def __init__(self, lat, lon, bofek_dir, staring_series_dir, RDMCR):
        self.lat = lat
        self.lon = lon
        self.RDMCR = RDMCR
        self.bofek_dir = bofek_dir
        self.staring_series_dir = staring_series_dir
        self.bofek_zip2_fp = bofek_dir / "BOFEK2020_GIS.7z"
        self.bofek_shape_fp = bofek_dir / "GIS" / "shp_files" / "bod_clusters.shp"
        self.all_profiles_fp = staring_series_dir / "AllProfiles_368.csv"
        self.soilcode_fp = self.staring_series_dir / "BodemCode.csv"
        self.staring_series_fp = self.staring_series_dir / "StaringReeksPARS_2018.csv"

        self.gdf_bofek = self.get_bofek2020_data()
        self.soilcode = self.get_soilcode()
        self.soilid = self.get_soilid()
        self.df_staring_blocks = self.get_staring_blocks_profile()
        self.df_vangenuchten = self.get_vangenuchten_profile()
        self.df_vangenuchten = self.get_van_genuchten_water_retention_curves()
        self.soil_yaml = self.get_soil_yaml()

    def get_bofek2020_data(self):
        if self.bofek_shape_fp.exists():
            pass
        else:
            response = requests.get(self.url_bofek2020)
            content = response.content
            response.close()
            z = zipfile.ZipFile(io.BytesIO(content))
            z.extractall(self.bofek_dir)
            z.close()
            s = py7zr.SevenZipFile(self.bofek_zip2_fp, 'r')
            s.extractall(self.bofek_dir)
            s.close()
        gdf_bofek = gpd.read_file(self.bofek_shape_fp)
        gdf_bofek = gdf_bofek.to_crs("EPSG:4326")
        return gdf_bofek
    def get_soilcode(self):
        min_lat = self.lat - 0.001
        max_lat = self.lat + 0.001
        min_lon = self.lon - 0.001
        max_lon = self.lon + 0.001
        gdf_bofek = self.gdf_bofek
        gdf_bofek = gdf_bofek.clip([min_lon, min_lat, max_lon, max_lat])

        cond = gdf_bofek.contains(Point(self.lon, self.lat))
        soilcode = gdf_bofek[cond].BODEMCODE.iloc[0]
        return soilcode

    def get_soilid(self):
        df_soilcode = pd.read_csv(self.soilcode_fp)
        cond = df_soilcode.BodemCode == self.soilcode
        soilid = df_soilcode[cond].iProfile.iloc[0]
        return soilid

    def get_staring_blocks_profile(self):
        df_profiles = pd.read_csv(self.all_profiles_fp)
        df_profile = df_profiles[df_profiles.iProfile == self.soilid]
        df_profile = df_profile.replace(99999, np.nan)
        df_profile = df_profile.replace(0, np.nan)
        df_profile = df_profile.dropna(axis=1)
        nlayer = int(df_profile.columns[-1][-1])
        soil_profile = SimpleNamespace(iProfile=[], layerid=[], minimum_depth=[], maximum_depth=[], thickness=[],
                                       isoil=[], staring_block=[])
        minimum_depth = 0
        for layerid in range(1, nlayer + 1):
            maximum_depth = df_profile[f"iZ{layerid}"].iloc[0]
            thickness = maximum_depth - minimum_depth
            isoil = df_profile[f"iSoil{layerid}"].iloc[0]
            staring_block = self.get_staring_block(isoil)
            soil_profile.iProfile.append(self.soilid)
            soil_profile.layerid.append(layerid)
            soil_profile.minimum_depth.append(minimum_depth)
            soil_profile.maximum_depth.append(maximum_depth)
            soil_profile.thickness.append(thickness)
            soil_profile.isoil.append(isoil)
            soil_profile.staring_block.append(staring_block)
            minimum_depth = maximum_depth

        if maximum_depth < self.RDMCR:
            maximum_depth = self.RDMCR
            thickness = maximum_depth - minimum_depth
            isoil = df_profile[f"iSoil{layerid}"].iloc[0]
            soil_profile.iProfile.append(self.soilid)
            soil_profile.layerid.append(layerid)
            soil_profile.minimum_depth.append(minimum_depth)
            soil_profile.maximum_depth.append(maximum_depth)
            soil_profile.thickness.append(thickness)
            soil_profile.isoil.append(isoil)
            soil_profile.staring_block.append(staring_block)

        df_staring_blocks = pd.DataFrame.from_dict(vars(soil_profile))
        return df_staring_blocks

    def get_staring_block(self,isoil):
        ntopsoils = 18
        if isoil <= ntopsoils:
            staring_block = f"B{str(isoil).zfill(1)}"
        else:
            staring_block = f"O{str(isoil - ntopsoils).zfill(1)}"
        return staring_block

    def get_vangenuchten_profile(self):
        df_vgn_profiles = pd.read_csv(self.staring_series_fp)
        df_vgn_profile = pd.merge(how='left',
                                  left=self.df_staring_blocks,
                                  right=df_vgn_profiles,
                                  left_on=["staring_block"],
                                  right_on=["Name"])
        return df_vgn_profile

    def get_van_genuchten_water_retention_curves(self):
        vgn = VanGenuchten()
        df = self.df_vangenuchten
        CONDfromPF_perlayer = []
        SMfromPF_perlayer = []
        for i in range(len(df)):
            CONDfromPF = []
            SMfromPF = []
            for j, pF in enumerate(self.pFs):
                r = vgn.calculate_soil_moisture_content(pF, df.Alpha.iloc[i], df.Npar.iloc[i], df.WCr.iloc[i],
                                                        df.WCs.iloc[i])
                SMfromPF.extend([pF, float(r)])
                r = vgn.calculate_log10_hydraulic_conductivity(pF, df.Alpha.iloc[i], df.Lambda.iloc[i],
                                                               df.Ksfit.iloc[i], df.Npar.iloc[i])
                CONDfromPF.extend([pF, float(r)])
            CONDfromPF_perlayer.append(CONDfromPF)
            SMfromPF_perlayer.append(SMfromPF)
        df["CONDfromPF"] = CONDfromPF_perlayer
        df["SMfromPF"] = SMfromPF_perlayer
        return df

    def get_soil_yaml(self):
        # below we generate the header of the soil input file as YAML input structure
        soil_input_yaml = f"""
            RDMSOL: {self.df_vangenuchten.thickness.sum()}
            SoilProfileDescription:
                PFWiltingPoint: {self.PFWiltingPoint}
                PFFieldCapacity: {self.PFFieldCapacity}
                SurfaceConductivity: {self.SurfaceConductivity}
                GroundWater: false
                SoilLayers:
            """

        # Here we generate the properties for each soil layer including layer thickness, hydraulic properties,
        # organic matter content, etc.
        nlayers = len(self.df_vangenuchten.thickness)
        ut = Util()
        for i in range(nlayers):
            s = f"""    - Thickness: {self.df_vangenuchten.thickness.iloc[i]}
                  CNRatioSOMI: {20.0}
                  CRAIRC: {0.01}
                  FSOMI: {0.03}
                  RHOD: {1.0}
                  Soil_pH: {5.}                              
                  SMfromPF: {self.df_vangenuchten.SMfromPF.iloc[i]}
                  CONDfromPF: {self.df_vangenuchten.CONDfromPF.iloc[i]}                  
            """
            soil_input_yaml += s

        # A SubSoilType needs to be defined. In this case we make the subsoil equal to the properties
        # of the deepest soil layer.
        soil_input_yaml += \
            f"""    SubSoilType:
                  Thickness: {self.df_vangenuchten.thickness.iloc[-1]}
                  CNRatioSOMI: {20.0}
                  CRAIRC: {0.01}
                  FSOMI: {0.03}
                  RHOD: {1.0}
                  Soil_pH: {5.}                                      
                  SMfromPF: {self.df_vangenuchten.SMfromPF[len(self.df_vangenuchten.SMfromPF) - 1]}
                  CONDfromPF: {self.df_vangenuchten.CONDfromPF[len(self.df_vangenuchten.CONDfromPF) - 1]}                   
            """
        soil_yaml = yaml.safe_load(soil_input_yaml)
        return soil_yaml

