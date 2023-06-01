import numpy as np
from scipy.signal import argrelextrema
from scipy.integrate import trapz


class SpecimenDINAnalysis:
    def __init__(self, stress, strain, lower_strain=0.2, upper_strain=0.4):
        self.stress = stress
        self.strain = strain
        self.lower_strain = lower_strain
        self.upper_strain = upper_strain
        self._Rplt = None
        self._Rplt_E = None
        self._ReH = None
        self._Ev = None
        self._Eff = None
        self._ReH_Rplt_ratio = None

    @property
    def Rplt(self):
        if self._Rplt is None:
            self._Rplt = self.calculate_Rplt()
        return self._Rplt

    @property
    def Rplt_E(self):
        if self._Rplt_E is None:
            self._Rplt_E = self.calculate_Rplt_E()
        return self._Rplt_E

    @property
    def ReH(self):
        if self._ReH is None:
            self._ReH = self.calculate_ReH()
        return self._ReH

    @property
    def Ev(self):
        if self._Ev is None:
            self._Ev = self.calculate_Ev()
        return self._Ev

    @property
    def Eff(self):
        if self._Eff is None:
            self._Eff = self.calculate_Eff()
        return self._Eff

    @property
    def ReH_Rplt_ratio(self):
        if self._ReH_Rplt_ratio is None:
            self._ReH_Rplt_ratio = self.calculate_ReH_Rplt_ratio()
        return self._ReH_Rplt_ratio

    def calculate_Rplt(self):
        idx_lower = (np.abs(self.strain - self.lower_strain)).argmin()
        idx_upper = (np.abs(self.strain - self.upper_strain)).argmin()
        return np.mean(self.stress[idx_lower:idx_upper])

    def calculate_Rplt_E(self):
        return (np.abs(self.stress - 1.3 * self.Rplt)).argmin()

    def calculate_ReH(self):
        comparator = np.greater
        indices = argrelextrema(self.stress, comparator)
        if len(indices[0]) > 0:
            return self.stress[indices[0][0]]
        else:
            return None

    def calculate_Ev(self):
        return trapz(self.stress[:self.Rplt_E], self.strain[:self.Rplt_E])

    def calculate_Eff(self):
        idx_lower = (np.abs(self.strain - self.lower_strain)).argmin()
        idx_upper = (np.abs(self.strain - self.upper_strain)).argmin()
        Rmax = np.max(self.stress[idx_lower:idx_upper])
        Aplt = self.strain[self.Rplt_E]
        return self.Ev / (Rmax * Aplt)

    def calculate_ReH_Rplt_ratio(self):
        if self.ReH is not None:
            return self.ReH / self.Rplt
        else:
            return None



# Assume stress and strain are your data
stress = np.array([...])
strain = np.array([...])

analysis = SpecimenDINAnalysis(stress, strain)

print("Rplt:", analysis.Rplt)
print("Rplt_E:", analysis.Rplt_E)
print("ReH:", analysis.ReH)
print("Ev:", analysis.Ev)
print("Eff:", analysis.Eff)
print("ReH/Rplt ratio:", analysis.ReH_Rplt_ratio)
