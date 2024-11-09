from pathlib import Path
from tkinter import filedialog

import pandas as pd

from standard_base.default_sample.sample import SampleGeneric
from standard_base.default_sample.sample_group import SampleGenericGroup
from standard_base.sample_factory import standard_registry
from tests.test_analyzable_entity import TestableAnalyzableEntity


def analyzably_entity_init():
    return TestableAnalyzableEntity(
        name="sample_entity",
        length=10,
        width=5,
        thickness=2,
        density=1,
        mass=1,
        force=pd.Series([0.5, 5, 30, 60]),
        displacement=pd.Series([1, 2, 3, 4]),
        time=pd.Series([1, 2, 3, 4]),
    )


def demo_import_single_entity():
    path = None
    while path is None:
        path = filedialog.askopenfile()

    from standard_base.io_management.flle_io_manager import FileIOManager

    if isinstance(entity.serializer.export_strategy, FileIOManager):
        new_entity = entity.serializer.export_strategy.import_object_from_file(
            return_class=TestableAnalyzableEntity, input_file=path.name
        )

        if isinstance(new_entity, TestableAnalyzableEntity):
            print(f"NEW Entity '{new_entity.name}' has an area of {new_entity.area:.2f} mm^2")
            print(f"Does the new entity equal the old entity? {entity == new_entity}")
        else:
            print("This is not a in the correct types")


def demo_export_single_entity():
    output_dir = Path.cwd() / "output"
    # path = filedialog.asksaveasfilename()
    entity.serializer.export(tracked_object=entity, output_path=output_dir)


def generic_sample_1_init():
    return SampleGeneric(
        name="Generic_Sample_1",
        length=100,  # mm
        width=50,  # mm
        thickness=70,  # mm
        mass=120,  # g
        force=pd.Series([0.5, 5, 30, 60]),  # N
        displacement=pd.Series([10, 20, 30, 40]),  # mm
        time=pd.Series([0.1, 0.2, 0.3, 0.4]),  # s
    )


def generic_sample_2_init():
    # Also use standard Reg for testing stake
    from standard_base.sample_factory import MechanicalTestStandards

    sample = standard_registry.get(MechanicalTestStandards.GENERAL_PRELIMINARY)

    if sample is None:
        raise ValueError("Sample not found in the standard registry")

    return sample(
        name="Generic_Sample_2",
        length=100,  # mm
        width=100,  # mm
        thickness=100,  # mm
        mass=100,  # g
        force=pd.Series([0.5, 5, 30, 60]),  # N
        displacement=pd.Series([20, 30, 40, 50]),  # mm
        time=pd.Series([0.5, 0.6, 0.7, 0.8]),  # s
    )


def generic_sample_group_init():
    samples = [generic_sample_1_init(), generic_sample_2_init()]
    return SampleGenericGroup(samples=samples)


def demo_export_generic_sample_group():
    output_dir = Path.cwd() / "output"
    sample_group = generic_sample_group_init()
    print(f"Entity '{sample_group.name}'")
    sample_group.serializer.export(tracked_object=sample_group, output_path=output_dir)


if __name__ == "__main__":
    entity = analyzably_entity_init()

    demo_export_generic_sample_group()
    print(f"The TestableAnalyzableEntity object is: {entity} was created successfully")
    # print(f"The TestableAnalyzableEntity object has the following properties: {entity.__dict__}")
    print(f"The TestableAnalyzableEntity serialized object is: {entity.serializer}")

    # Begin testing the serialization of the TestableAnalyzableEntity object

    # export propertie Area

    print(f"Entity '{entity.name}' has an area of {entity.area:.2f} mm^2")
    print(f"Entity '{entity.name}' {entity.__class__.area.fget._is_exportable}")
    print(f"Entity '{entity.name}' {entity.__class__.area.fget._export_metadata}")

    # demo_export_single_entity()

    demo_import_single_entity()
