from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    database_url: str = "postgresql+psycopg://bhoomi:bhoomi@localhost:5433/bhoomisync"
    test_database_url: str = "postgresql+psycopg://bhoomi:bhoomi@localhost:5433/bhoomisync_test"
    project_crs: str = "EPSG:32643"
    data_dir: Path = REPO_DIR / "data" / "demo"
    validation_dir: Path = REPO_DIR / "data" / "validation"
    demo_city: str = "pune"
    upload_dir: Path = REPO_DIR / "data" / "uploads"
    max_upload_bytes: int = 20 * 1024 * 1024
    weights: dict[str, float] = {
        "geometry": 0.30,
        "centroid": 0.20,
        "area": 0.15,
        "shape": 0.15,
        "attribute": 0.10,
        "temporal": 0.10,
    }
    high_threshold: float = 0.85
    review_threshold: float = 0.60
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


settings = Settings()

DISCLAIMER = "Decision-support only — not a legal determination of ownership."
