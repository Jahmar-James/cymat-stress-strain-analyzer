from standard_validator import BaseStandardValidator, MechanicalTestStandards, register_validator


@register_validator(MechanicalTestStandards.GENERAL_PRELIMINARY)
class GeneralPreliminaryValidator(BaseStandardValidator):
    def __init__(self):
        super().__init__()
        # No specific validation methods for this standard
        # This result in the the feilds being skipped during validation
        self.data_validation_methods = {}
        self.column_name_requirements = {}
        self.column_interval_requirements = {}
