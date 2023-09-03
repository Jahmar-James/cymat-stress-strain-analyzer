
from sqlalchemy.orm import registry
from sqlalchemy_continuum import make_versioned

# Call this before defining your mapped classes.
make_versioned()

mapper_registry = registry()
Base = mapper_registry.generate_base()

class BaseORMVersioned(Base):
    """Base class for versioned tables."""
    __abstract__ = True
    __versioned__ = {}
    
    def __repr__(self):
        return f'ORM:<{self.__class__.__name__} {self.id}>'