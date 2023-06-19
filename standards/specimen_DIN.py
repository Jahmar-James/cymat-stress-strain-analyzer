import numpy as np
from scipy.signal import argrelextrema
from scipy.integrate import trapz


class SpecimenDINAnalysis:
    def __init__(self, stress, strain, lower_strain=0.2, upper_strain=0.4):
        self.stress = np.array(stress)# Compressive Stress (Rd)
        self.strain = np.array(strain) # Compressive Strain (ed)
        self.lower_strain = lower_strain
        self.upper_strain = upper_strain
        self._Rplt = None # Plateau stress Arithmetical mean of the stresses between  upper and lower ~ IYS
        self._Rplt_E = None # Plateau End (Rplt-E) = 1.3 _Rplt 
        self._Aplt_E = None # Compressive Strain at Plateau End (Aplt-E)
        self._ReH = None # Upper Compressive Yield Strength stress corresponding to the first local maximum
        self._AeH = None # corresponding strian
        self._Ev = None # Specific Energy Absorption (Ev) - area up to plateau end ~ Toughness
        self._Eff = None # Specific Energy Absorption Efficiency (Eff)
        self._ReH_Rplt_ratio = None # Compressive yield strength ratio (ReH/Rplt) ~ ductility
        self._Rp1 = None # Compressive Yield Point (Rp1)
        self._m = None #  gradient (m) ~ Resilience:

    #TO DO adjust EV to start for 0
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

    # ValueError("the 'mode' parameter is not supported in the pandas implementation of take()")
    @property
    def ReH(self):
        if self._ReH is None:
            self._ReH = self.calculate_ReH()
        return self._ReH

    @property
    def Ev(self):
        if self._Ev is None:
            self._Ev = self.calculate_Ev(self.lower_strain)
        return self._Ev
    
    @property
    def E20(self):
        return self.calculate_Ev(0.2)

    @property
    def E40(self):
        return self.calculate_Ev(0.4)

    @property
    def E60(self):
        return self.calculate_Ev(0.6)

    @property
    def Eff(self):
        if self._Eff is None:
            self._Eff = self.calculate_Eff()
        return self._Eff
    #ValueError("the 'mode' parameter is not supported in the pandas implementation of take()")
    # Side affect of ReH
    @property
    def ReH_Rplt_ratio(self):
        if self._ReH_Rplt_ratio is None:
            self._ReH_Rplt_ratio = self.calculate_ReH_Rplt_ratio()
        return self._ReH_Rplt_ratio
    
    @property
    def Aplt_E(self):
        if self._Aplt_E is None:
            self._Aplt_E = self.calculate_Aplt_E()
        return self._Aplt_E

    #error ValueError("the 'mode' parameter is not supported in the pandas implementation of take()") 
    @property
    def AeH(self):
        if self._AeH is None:
            self._AeH = self.calculate_AeH()
        return self._AeH

    @property
    def Rp1(self):
        if self._Rp1 is None:
            self._Rp1 = self.calculate_Rp1()
        return self._Rp1

    @property
    def m(self):
        if self._m is None:
            self._m = self.calculate_m()
        return self._m

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

    def calculate_Ev(self, compression):
        idx = (np.abs(self.strain - compression)).argmin()
        return trapz(self.stress[:idx], self.strain[:idx])

    def calculate_Eff(self):
        idx_lower = (np.abs(self.strain - self.lower_strain)).argmin()
        idx_upper = (np.abs(self.strain - self.upper_strain)).argmin()
        Rmax = np.max(self.stress[idx_lower:idx_upper]) or 1
        if Rmax == 1:
            return None
        Aplt = self.strain[self.Rplt_E]
        return self.Ev / (Rmax * Aplt)

    def calculate_ReH_Rplt_ratio(self):
        if self.ReH is not None:
            return self.ReH / self.Rplt
        else:
            return None
        
    def calculate_Aplt_E(self):
        return self.strain[self.Rplt_E]

    def calculate_AeH(self):
        indices = argrelextrema(self.stress, np.greater)
        if len(indices[0]) > 0:
            return self.strain[indices[0][0]]
        else:
            return None

    def calculate_Rp1(self):
        return self.stress[np.abs(self.strain - 0.01).argmin()]

    def calculate_m(self):
        idx_R20 = np.abs(self.stress - 0.2 * self.Rplt).argmin()
        idx_R70 = np.abs(self.stress - 0.7 * self.Rplt).argmin()
        return (self.stress[idx_R70] - self.stress[idx_R20]) / (self.strain[idx_R70] - self.strain[idx_R20])
