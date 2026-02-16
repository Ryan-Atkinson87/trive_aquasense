from dataclasses import dataclass
from typing import Optional
import time


@dataclass(frozen=True)
class DisplayStatus:
    device_name: str
    water_temperature: Optional[float]
    air_temperature: Optional[float]
    air_humidity: Optional[float]
    water_flow: Optional[float]
    timestamp_utc: float

    @classmethod
    def from_snapshot(cls, snapshot: dict) -> "DisplayStatus":
        values = snapshot.get("values", {})

        return cls(
            device_name=snapshot.get("device_name", "unknown"),
            water_temperature=values.get("water_temperature"),
            air_temperature=values.get("air_temperature"),
            air_humidity=values.get("air_humidity"),
            water_flow=values.get("water_flow"),
            timestamp_utc=snapshot.get("ts", time.time()),
        )
