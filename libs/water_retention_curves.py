import numpy as np

class VanGenuchten():
    def calculate_water_potential_form_pf(self, pF):
        psi = np.power(10, pF)
        return psi

    def calculate_soil_moisture_content(self, pF, alpha, n, theta_r, theta_s):
        psi = self.calculate_water_potential_form_pf(pF)
        soil_moisture_content = theta_r + (theta_s - theta_r) / np.power(1 + (np.power(alpha * psi, n)), 1 - 1 / n)
        return soil_moisture_content

    def calculate_log10_hydraulic_conductivity(self, pF, alpha, labda, k_sat, n):
        psi = self.calculate_water_potential_form_pf(pF)
        m = 1 - 1 / n;
        ah = alpha * psi
        h1 = np.power(1 + np.power(ah, n), m)
        h2 = np.power(ah, n - 1)
        denom = np.power(1 + np.power(ah, n), m * (labda + 2));
        k_h = k_sat * np.power(h1 - h2, 2) / denom
        COND = np.log10(k_h)
        return COND

    def make_string_table(self, XY_table):
        """Converts a list of X,Y pairs into a formatted string table.
        """
        s = "["
        for x, y in zip(XY_table[0::2], XY_table[1::2]):
            s += f"{x:4.1f}, {y:7.4f}, "
        s += "]"
        s = s.replace("  ", " ")
        return s