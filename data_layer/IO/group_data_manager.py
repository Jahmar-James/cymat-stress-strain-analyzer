# app/data_layer/IO/group_data_manager.py

class SampleGroupDataManager:
    """This class could handle bulk data operations for the entire SampleGroup, like saving all specimens to a database or loading them."""
    def __init__(self, repository=None, control_metrics_provider=None, excel_exporter=None):
            self.repository = repository or SampleGroupRepository()
            self.control_metrics = control_metrics_provider or ControlProcessMetrics()
            self.excel_exporter = excel_exporter or SampleGroupExcelExporter()