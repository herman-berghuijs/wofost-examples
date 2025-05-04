import pandas as pd
import requests
import sqlalchemy as sa
import time
from pcse.input import WOFOST81SiteDataProvider_SNOMIN, YAMLCropDataProvider, CSVWeatherDataProvider
from libs.pedotransferfunctions import PedotransferFunctionsWosten
from libs.water_retention_curves import VanGenuchten
from types import SimpleNamespace
from libs.util import Util
import yaml

pct_to_frac = 0.01
pml_to_pct = 0.1

class SoilGridsDataProvider():
    vgnd = None
    soilgridsdresult = None
    soild = None
    vgnd = None
    request_url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    soilgrids_vars = ["bdod", "clay", "phh2o", "sand", "silt", "soc", "nitrogen"]
    soilgrids_soillayers = ['0-5cm', '5-15cm', '15-30cm', '30-60cm', '60-100cm']

    CRAIRC = 0.03
    f_C_to_OM = 0.58
    lower_boundary_topsoil = 30.
    PFFieldCapacity = 2.0
    PFWiltingPoint = 4.2
    pFs = [-1.0, 1.0, 1.3, 1.7, 2.0, 2.3, 2.4, 2.7, 3.0, 3.3, 3.7, 4.0, 4.2, 6.0]
    SurfaceConductivity = 70.

    def __init__(self, lat, lon, RDMCR):
        p1 = {"lat": lat, "lon": lon}
        props = {"property": self.soilgrids_vars, "depth": self.soilgrids_soillayers}
        # Necessary, because the SoilGrid API only allows a maximum of 5 requests per minute
        status_code = 429
        while status_code == 429:
            res = requests.get(self.request_url, params={**p1, **props})
            status_code = res.status_code
            if(status_code == 429):
                print("Too many requests to SoilGrids API. After 15 seconds, another attempt is made to retrieve SoilGrids data")
                time.sleep(15)
        self.soilgridsdresult = res.json()
        self.get_soilgridsd(lat, lon, RDMCR)
        self.calculate_derived_soil_properties()
        self.get_vangenuchten_parameters()
        self.get_van_genuchten_water_retention_curves()
        self.get_soil_yaml()

    def get_soil_yaml(self):
        vgnd = SimpleNamespace(**self.vgnd)
        soild = SimpleNamespace(**self.soild)
        # below we generate the header of the soil input file as YAML input structure
        soil_input_yaml = f"""
            RDMSOL: {sum(list(vgnd.Thickness.values()))}
            SoilProfileDescription:
                PFWiltingPoint: {self.PFFieldCapacity}
                PFFieldCapacity: {self.PFWiltingPoint}
                SurfaceConductivity: {self.SurfaceConductivity}
                GroundWater: false
                SoilLayers:
            """

        # Here we generate the properties for each soil layer including layer thickness, hydraulic properties,
        # organic matter content, etc.
        nlayers = len(vgnd.Thickness)
        ut = Util()
        for i in range(nlayers):
            s = f"""    - Thickness: {vgnd.Thickness[i]}
                  CNRatioSOMI: {soild.CNRatioSOMI[i]}
                  CRAIRC: {soild.CRAIRC[i]}
                  FSOMI: {soild.FSOMI[i]}
                  RHOD: {soild.bdod[i]}
                  Soil_pH: {soild.phh2o[i]}
                  SMfromPF: {vgnd.SMfromPF[i]}
                  CONDfromPF: {vgnd.CONDfromPF[i]}
            """
            soil_input_yaml += s

        # A SubSoilType needs to be defined. In this case we make the subsoil equal to the properties
        # of the deepest soil layer.
        soil_input_yaml += \
            f"""    SubSoilType:
                  CNRatioSOMI: {list(soild.CNRatioSOMI)[-1]}
                  CRAIRC: {list(soild.CRAIRC)[-1]}
                  FSOMI: {list(soild.FSOMI)[-1]}
                  RHOD: {list(soild.bdod)[-1]}
                  Soil_pH: {list(soild.phh2o)[-1]}
                  Thickness: {list(soild.CNRatioSOMI)[-1]}
                  SMfromPF: {vgnd.SMfromPF[len(vgnd.SMfromPF) - 1]}
                  CONDfromPF: {vgnd.CONDfromPF[len(vgnd.CONDfromPF) - 1]}
            """
        soil_yaml = yaml.safe_load(soil_input_yaml)
        self.soil_yaml = soil_yaml

    def get_soilgridsd(self, lat, lon, RDMCR):
        soilgridsd = {}
        soilgridsd["latitude"] = []
        soilgridsd["longitude"] = []
        soilgridsd["layerid"] = []
        soilgridsd["zmin"] = []
        soilgridsd["zmax"] = []
        soilgridsd["Thickness"] = []
        for j in range(0, len(self.soilgrids_soillayers)):
            zmin = self.get_zmin(self.soilgrids_soillayers[j])
            zmax = self.get_zmax(self.soilgrids_soillayers[j])
            soilgridsd["layerid"].append(j)
            soilgridsd["zmin"].append(zmin)
            soilgridsd["zmax"].append(zmax)
            soilgridsd["Thickness"].append(zmax - zmin)
            soilgridsd["latitude"].append(lat)
            soilgridsd["longitude"].append(lon)
        for j, var in enumerate(self.soilgrids_vars):
            var_name = self.soilgridsdresult['properties']["layers"][j]['name']
            if (var_name in self.soilgrids_vars):
                soilgridsd[var_name] = []
                for k in range(0, len(self.soilgrids_soillayers)):
                    raw_value = self.soilgridsdresult['properties']["layers"][j]["depths"][k]["values"]["mean"]
                    d_factor = self.soilgridsdresult["properties"]["layers"][j]["unit_measure"]["d_factor"]
                    value = raw_value / d_factor
                    soilgridsd[var_name].append(value)
        if (soilgridsd["zmax"][-1] < RDMCR):
            zmin = soilgridsd["zmax"][-1]
            dz = RDMCR - zmin
            zmax = zmin + dz
            layerid = soilgridsd["layerid"][-1] + 1
            soilgridsd["layerid"].append(layerid)
            soilgridsd["zmin"].append(zmin)
            soilgridsd["zmax"].append(zmax)
            soilgridsd["Thickness"].append(dz)
            soilgridsd["latitude"].append(lat)
            soilgridsd["longitude"].append(lon)
            for var in self.soilgrids_vars:
                soilgridsd[var].append(soilgridsd[var][-1])
        self.soild = soilgridsd

    def calculate_derived_soil_properties(self):
        df_soil = pd.DataFrame.from_dict(self.soild)
        df_soil["OM"] = df_soil.soc.copy() * pml_to_pct * self.f_C_to_OM
        df_soil["FSOMI"] = df_soil.OM.copy() * pct_to_frac
        df_soil["CNRatioSOMI"] = df_soil.soc.copy() / df_soil.nitrogen.copy()
        df_soil["CRAIRC"] = self.CRAIRC
        self.soild = df_soil.to_dict()

    def get_vangenuchten_parameters(self):
        ptfw = PedotransferFunctionsWosten()
        df_soilgridsd = pd.DataFrame(self.soild)
        df_soilgridsd["is_topsoil"] = df_soilgridsd.apply(lambda x:
                                                          ptfw.calculate_isTopsoil(x.zmin,
                                                                                   x.zmax,
                                                                                   self.lower_boundary_topsoil),
                                            axis=1)
        df_vgn = pd.DataFrame()
        df_vgn["layerid"] = df_soilgridsd["layerid"]
        df_vgn["zmin"] = df_soilgridsd["zmin"]
        df_vgn["zmax"] = df_soilgridsd["zmax"]
        df_vgn["Thickness"] = df_soilgridsd.zmax - df_soilgridsd.zmin
        df_vgn["theta_r"] = 0.01
        df_vgn["is_topsoil"] = df_soilgridsd.apply(lambda x:
                                              ptfw.calculate_isTopsoil(x.zmin, x.zmax, self.lower_boundary_topsoil),
                                            axis=1)
        df_vgn["alpha"] = df_soilgridsd.apply(lambda x:
                                         ptfw.calculate_alpha(x.clay, x.bdod, x.silt, x.OM, x.is_topsoil),
                                       axis=1)
        df_vgn["k_sat"] = df_soilgridsd.apply(lambda x:
                                         ptfw.calculate_k_sat(x.clay, x.bdod, x.silt, x.OM, x.is_topsoil),
                                       axis=1)
        df_vgn["labda"] = df_soilgridsd.apply(lambda x:
                                         ptfw.calculate_lambda(x.clay, x.bdod, x.silt, x.OM, x.is_topsoil),
                                       axis=1)
        df_vgn["n"] = df_soilgridsd.apply(lambda x:
                                     ptfw.calculate_n(x.clay, x.bdod, x.silt, x.OM, x.is_topsoil),
                                   axis=1)
        df_vgn["theta_s"] = df_soilgridsd.apply(lambda x:
                                           ptfw.calculate_theta_s(x.clay, x.bdod, x.silt, x.OM, x.is_topsoil),
                                         axis=1)
        self.vgnd = df_vgn.to_dict()

    def get_van_genuchten_water_retention_curves(self):
        vgn = VanGenuchten()
        df_vgn = pd.DataFrame.from_dict(self.vgnd)
        CONDfromPF_perlayer = []
        SMfromPF_perlayer = []
        for i in range(len(df_vgn)):
            CONDfromPF = []
            SMfromPF = []
            for j, pF in enumerate(self.pFs):
                r = vgn.calculate_soil_moisture_content(pF, df_vgn.alpha.iloc[i], df_vgn.n.iloc[i], df_vgn.theta_r.iloc[i],
                                                        df_vgn.theta_s.iloc[i])
                SMfromPF.extend([pF, float(r)])
                r = vgn.calculate_log10_hydraulic_conductivity(pF, df_vgn.alpha.iloc[i], df_vgn.labda.iloc[i],
                                                               df_vgn.k_sat.iloc[i], df_vgn.n.iloc[i])
                CONDfromPF.extend([pF, float(r)])
            CONDfromPF_perlayer.append(CONDfromPF)
            SMfromPF_perlayer.append(SMfromPF)
        df_vgn["CONDfromPF"] = CONDfromPF_perlayer
        df_vgn["SMfromPF"] = SMfromPF_perlayer
        self.vgnd = df_vgn.to_dict()

    def get_soild(self):
        return 0

    def get_zmin(self, val):
        zmin = float(val.split("-")[0])
        return zmin

    def get_zmax(self, val):
        zmax = float(val.split("-")[1].replace("cm",""))
        return zmax
