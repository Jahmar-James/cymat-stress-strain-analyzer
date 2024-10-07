import pandas as pd

from tests.test_analyzable_entity import TestableAnalyzableEntity


def analyzably_entity_init():
    return TestableAnalyzableEntity(
        name="test",
        length=10,
        width=5,
        thickness=2,
        density=1,
        mass=1,
        force=pd.Series([1, 2, 3, 4]),
        displacement=pd.Series([1, 2, 3, 4]),
        time=pd.Series([1, 2, 3, 4]),
    )


if __name__ == "__main__":
    entity = analyzably_entity_init()

    print(f"The TestableAnalyzableEntity object is: {entity} was created successfully")
    # print(f"The TestableAnalyzableEntity object has the following properties: {entity.__dict__}")
    print(f"The TestableAnalyzableEntity serialized object is: {entity.serializer}")

    # Begin testing the serialization of the TestableAnalyzableEntity object
    from pathlib import Path

    # export propertie Area

    print(f"Entity '{entity.name}' has an area of {entity.area:.2f} mm^2")
    print(f"Entity '{entity.name}' {entity.__class__.area.fget._is_exportable}")
    print(f"Entity '{entity.name}' {entity.__class__.area.fget._export_metadata}")

    output_dir = Path.cwd() / "output"
    entity.serializer.export(tracked_object=entity, output_dir=output_dir)
