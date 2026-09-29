"""City registry: the multi-city configuration layer (spec v2 §30). One demo city, one synthetic
validation city, the rest planned. Adding a city later = one entry + a dataset."""

from __future__ import annotations

CITIES: list[dict] = [
    {"id": "ahmedabad", "name": "Ahmedabad", "state": "Gujarat", "lon": 72.5714, "lat": 23.0225, "status": "planned"},
    {"id": "delhi", "name": "Delhi", "state": "Delhi", "lon": 77.2090, "lat": 28.6139, "status": "planned"},
    {"id": "mumbai", "name": "Mumbai", "state": "Maharashtra", "lon": 72.8777, "lat": 19.0760, "status": "planned"},
    {"id": "bengaluru", "name": "Bengaluru", "state": "Karnataka", "lon": 77.5946, "lat": 12.9716, "status": "planned"},
    {"id": "hyderabad", "name": "Hyderabad", "state": "Telangana", "lon": 78.4867, "lat": 17.3850, "status": "planned"},
    {"id": "pune", "name": "Pune", "state": "Maharashtra", "lon": 73.8567, "lat": 18.5204, "status": "demo"},
    {"id": "jaipur", "name": "Jaipur", "state": "Rajasthan", "lon": 75.7873, "lat": 26.9124, "status": "planned"},
    {"id": "surat", "name": "Surat", "state": "Gujarat", "lon": 72.8311, "lat": 21.1702, "status": "validation"},
]

DATASET_LABELS = {"demo": "Demo / Synthetic Dataset", "validation": "Synthetic validation dataset"}


def get_city(city_id: str) -> dict | None:
    return next((c for c in CITIES if c["id"] == city_id), None)
