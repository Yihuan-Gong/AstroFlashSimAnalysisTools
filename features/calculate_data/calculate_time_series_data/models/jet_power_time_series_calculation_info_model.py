from dataclasses import dataclass

from .time_series_calculation_info_model import TimeSeriesCalculationInfoModel

@dataclass
class JetPowerTimeSeriesCalculationInfoModel \
    (TimeSeriesCalculationInfoModel):
    smoothingMyr: float = None
    agnDataFileName: str = "agn_0000000000000001.dat"