# app/data_layer/IO/repositories/base_repository.py

from typing import Optional, Tuple, Iterator
from contextlib import contextmanager
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.sql.functions import func

from .base_orm import BaseORMVersioned

# DATA ACCESS (REPOSITORIES) CRUD OPERATIONS

# A utility to optionally provide a session or create a new one
@contextmanager
def provide_session(external_session=None, engine = None) -> Iterator[Session]:
    if external_session:
        yield external_session
    else:
        session = sessionmaker(bind=engine)
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

# CRUD Operations
class BaseRepository:
    """Base repository class to provide common CRUD operations. From ORM objects to Database (DAO)"""
    def __init__(self, model: 'BaseORMVersioned'):
        self.model = model

    def create_entity(self, entity: 'BaseORMVersioned', current_session: Optional[Session] = None) -> Tuple[bool, int]:
        with provide_session(current_session) as active_session:
            try:
                active_session.add(entity)
                active_session.flush() 
                return True, entity.id
            except SQLAlchemyError as e:
                print(f"Error adding entity ({entity}): {e}")
                return False, -1

    def retrieve_entity_by_id(self, entity_id: int, current_session: Optional[Session] = None) -> Optional['BaseORMVersioned']:
        with provide_session(current_session) as active_session:
            fetch_query = select(self.model).where(self.model.id == entity_id)
            fetched_entity = active_session.execute(fetch_query).scalars().first()
            if fetched_entity:
                active_session.expunge(fetched_entity)  # so that object isn't tied to session
                return fetched_entity
            else:
                return None
            
    def retrieve_entity_by_attribute(self, attribute, value, current_session: Optional[Session] = None) -> Optional['BaseORMVersioned']:
        with provide_session(current_session) as active_session:
            fetch_query = select(self.model).where(attribute == value)
            fetched_entity = active_session.execute(fetch_query).scalars().first()
            if fetched_entity:
                active_session.expunge(fetched_entity)  # so that object isn't tied to session
                return fetched_entity
            else:
                return None
            
    def retrieve_all_entities(self, current_session: Optional[Session] = None) -> Iterator['BaseORMVersioned']:
        with provide_session(current_session) as active_session:
            fetch_query = select(self.model)
            fetched_entities = active_session.execute(fetch_query).scalars()
            for entity in fetched_entities:
                active_session.expunge(entity)
                yield entity

    def update_entity(self, entity: 'BaseORMVersioned', current_session: Optional[Session] = None) -> bool:
        with provide_session(current_session) as active_session:
            try:
                active_session.merge(entity)
                return True
            except SQLAlchemyError as e:
                print(f"Error updating entity: {e}")
                return False

    def delete_entity_by_id(self, entity_id: int, current_session: Optional[Session] = None) -> bool:
        with provide_session(current_session) as active_session:
            entity = self.retrieve_entity_by_id(entity_id, active_session)
            if not entity:
                print(f"Entity with ID {entity_id} does not exist. Cannot delete.")
                return False
            try:
                active_session.delete(entity)
                return True
            except SQLAlchemyError as e:
                print(f"Error deleting entity: {e}")
                return False
            
    def count_all_entities(self, current_session: Optional[Session] = None) -> int:
        with provide_session(current_session) as active_session:
            count_query = select(func.count()).select_from(self.model)
            entity_count = active_session.scalar(count_query)
            return entity_count
        
 