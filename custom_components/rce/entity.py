from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

class RCEBaseEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)

        # jedno źródło prawdy — coordinator
        self._attr_device_info = coordinator.device_info

        # przydatne dla unique_id w encjach potomnych
        self._entry_id = entry_id

    @property                                             
    def available(self) -> bool:
        return bool(self.coordinator.data)
