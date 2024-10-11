from standard_base.validation.base_standard_validator import BaseStandardValidator


class GeneralPreliminaryValidator(BaseStandardValidator):
    def __init__(self):
        super().__init__()
        # No specific validation methods for this standard
        # This result in the the feilds being skipped during validation
        self.data_validation_methods = {}
        self.column_name_requirements = {}
        self.column_interval_requirements = {}
        self.column_interval_requirements = {}
        self.sample_properties_validation_methods = {}
