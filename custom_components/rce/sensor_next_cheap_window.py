from homeassistant.components.sensor import SensorDeviceClass

class RCENextCheapWindowSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._attr_unique_id = f"rce_{entry_id}_next_cheap_window"
        self._attr_name = "Next cheap energy window"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "RCE PSE",
            "manufacturer": "PSE",
        }

    @property
    def native_value(self) -> datetime | None:
        mask = self.coordinator.data.get("cheap_mask", [])
        if not mask:
            return None

        res = self.coordinator.data.get("resolution", RESOLUTION_15M)
        factor = 4 if res == RESOLUTION_15M else 1
        
        now = dt_util.now()
        current_idx = now.hour * factor + (now.minute // (60 // factor))

        for i in range(current_idx + 1, len(mask)):
            if mask[i]:
                hour = i // factor
                minute = (i % factor) * (60 // factor)
                
                return now.replace(
                    hour=hour, 
                    minute=minute, 
                    second=0, 
                    microsecond=0
                )

        return None
