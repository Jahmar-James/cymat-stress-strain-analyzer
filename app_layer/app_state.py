# app/app_layer/app_state.py

from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from data_layer.models.specimen import Specimen 
    from data_layer.models.sample_group import SampleGroup
    from data_layer.models.analyzable_entity import AnalyzableEntity


class AppVariables(BaseModel):
    """
    Contain app varibles, provide validation. 
    The Subjet of Observer pattern. 
    """
    # Data / Model
    specimens: List[Specimen] = Field(default=[], description="A list containing all the loaded specimens.")
    sample_groups: List[SampleGroup] = Field(default=[], description="A list containing all the loaded sample groups.")

    # Iddexs to selected specimens and sample groups
    current_specimen_index: Optional[int] = Field(default=None, description="Index of the currently selected specimen.")
    current_sample_group_index: Optional[int] = Field(default=None, description="Index of the currently selected sample group.")
    selected_specimen_indices: List[int] = Field(default=[], description="List of selected specimen indices.")
    selected_sample_group_indices: List[int] = Field(default=[], description="List of selected sample group indices.")
    
    # Analysis
    analysis_type: Optional[str] = Field(default=None, description="The type of analysis being performed. ie. ISO 13314 ")
    analysis_parameters: Optional[dict] = Field(default=None, description="Parameters for the analysis.")
    analysis_result: Optional[dict] = Field(default=None, description="The result of the analysis.")
    
    # Process flags
    export_in_progress: bool = Field(default=False, description="Flag indicating whether an export is in progress.")
    
    # Observer pattern
    observers = []
    
    def register_observer(self, observer):
        self.observers.append(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.update()
    
    def __init__(self, **data):
        super().__init__(**data)
        self._initialized = True
        self._changed_attributes = set()
    
     # Avoid recursive notification when setting 'observers'
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if hasattr(self, '_initialized') and self._initialized and name != "observers":
            self._changed_attributes.add(name)
            self.notify_observers()
    
    def get_and_reset_changed_attributes(self):
        changes = self._changed_attributes.copy()
        self._changed_attributes.clear()
        return changes
    
    def _add_item(self, item, item_list: list, item_name = "Item"):
        """
        A private method to add an item to a specified list while avoiding duplicates.
        """
        if item not in item_list:
            item_list.append(item)
            self.notify_observers()
        else:
            raise ValueError("{item_name} already exists in the list")
    
    def add_specimen(self, specimen: Specimen, item_name = "Specimen"):
        self._add_item(specimen, self.specimens, f"{item_name}: {specimen.name}")
    
    def add_sample_group(self, sample_group: SampleGroup, item_name = "Sample group"):
        self._add_item(sample_group, self.sample_groups , f"{item_name}: {sample_group.name}")
        
    def _remove_items_by_indices(self, indices: List[int], item_list: List[AnalyzableEntity], current_index: int, selected_indices: List[int]) -> int:
        """ 
        A private method to remove items based on a list of indices, and update the current and selected indices.
        Returns the new current index.
        """
        # Make an immutable copy of the indices list
        indices = tuple(indices)

        for index in indices:
            try:
                del item_list[index]
            except IndexError:
                raise IndexError(f"Index ({index}) is out of range of the list {item_list}")

        # Update current and selected indices
        if current_index in indices:
            current_index = max(len(item_list) - 1, 0) if item_list else None
        selected_indices[:] = [idx for idx in selected_indices if idx not in indices]

        return current_index
    
    def remove_specimens_by_indices(self, indices: List[int]):
        """
        Removes specimens based on a list of indices.
        """
        self.current_specimen_index = self._remove_items_by_indices(
            indices, self.specimens, self.current_specimen_index, self.selected_specimen_indices
        )
        self.notify_observers()
    
    def remove_sample_groups_by_indices(self, indices: List[int]):
        """
        Removes sample groups based on a list of indices.
        """
        self.current_sample_group_index = self._remove_items_by_indices(
            indices, self.sample_groups, self.current_sample_group_index, self.selected_sample_group_indices
        )
        self.notify_observers() 
        
    def _set_current_analyzable_entity(self, entity: Optional['AnalyzableEntity'] = None, index_of_entity: Optional[int] = None):
        # pass in either entity or index_of_entity
        # if the entity is provided, find the index of the entity
        def get_index_of_entity(entity):
            index_of_entity = None
            if entity:
                if isinstance(entity, Specimen):
                    index_of_entity = self.specimens.index(entity)
                elif isinstance(entity, SampleGroup):
                    index_of_entity = self.sample_groups.index(entity)
            return index_of_entity
        
        if entity:
            index_of_entity = get_index_of_entity(entity)
        
        return index_of_entity
        
    def set_current_specimen(self, specimen: Optional[Specimen] = None, index_of_specimen: Optional[int] = None):
        self.current_specimen_index = self._set_current_analyzable_entity(specimen, index_of_specimen) 
    
    def set_current_sample_group(self, sample_group: Optional[SampleGroup] = None, index_of_sample_group: Optional[int] = None):
        self.current_sample_group_index = self._set_current_analyzable_entity(sample_group, index_of_sample_group)              

    @property
    def current_specimen(self) -> Optional[Specimen]:
        return self.specimens[self.current_specimen_index] if self.current_specimen_index is not None else None

    @property
    def current_sample_group(self) -> Optional[SampleGroup]:
        return self.sample_groups[self.current_sample_group_index] if self.current_sample_group_index is not None else None


    