# app/data_layer/__init__.py,

from pint import UnitRegistry
from collections import namedtuple

unit_registry = UnitRegistry()
unit_registry.define('inch = 25.4 * mm = in')
unit_registry.define('kN = 1000 * N = kN')
unit_registry.define('MPa = 1000 * kPa = MPa')
unit_registry.define('psi = 6894.76 * Pa = psi')
unit_registry.define('ksi = 1000 * psi = ksi')
unit_registry.define('mm2 = mm**2 = mm2')
unit_registry.define('mm3 = mm**3 = mm3')
unit_registry.define('inch2 = inch**2 = inch2')
unit_registry.define('inch3 = inch**3 = inch3')
unit_registry.define('m2 = m**2 = m2')
unit_registry.define('m3 = m**3 = m3')
unit_registry.define('ft2 = ft**2 = ft2')




