import pytest

from app.ingest.normalize import normalize
from app.ingest.readers import IngestError, read_source


def test_geojson_32643_detected(demo_dir):
    gdf, crs = read_source(demo_dir / "cadastral.geojson")
    assert crs == "EPSG:32643" and len(gdf) == 1000


def test_csv_latlon_detected_and_normalized(demo_dir):
    gdf, crs = read_source(demo_dir / "revenue.csv")
    assert crs == "EPSG:4326"
    res = normalize(gdf)
    assert res.source_crs == "EPSG:4326" and res.target_crs == "EPSG:32643"
    x, y = res.gdf.geometry.iloc[0].x, res.gdf.geometry.iloc[0].y
    assert 350_000 < x < 400_000 and 2_030_000 < y < 2_070_000
    assert "latitude" not in res.gdf.columns


def test_municipal_aligns_with_cadastral_after_normalize(demo_dir):
    cad = normalize(read_source(demo_dir / "cadastral.geojson")[0]).gdf
    mun = normalize(read_source(demo_dir / "municipal.geojson")[0]).gdf
    assert cad.total_bounds[0] == pytest.approx(mun.total_bounds[0], abs=20)


def test_csv_with_utm_values_as_latlon_rejected(tmp_path):  # Review Focus 1
    p = tmp_path / "bad.csv"
    p.write_text("id,lat,lon\n1,2047900,373000\n")
    with pytest.raises(IngestError, match="out of range for EPSG:4326"):
        read_source(p)


def test_geojson_without_crs_but_projected_values_rejected(tmp_path):  # Review Focus 1
    p = tmp_path / "bad.geojson"
    p.write_text('{"type":"FeatureCollection","features":[{"type":"Feature","properties":{},'
                 '"geometry":{"type":"Point","coordinates":[373000,2047900]}}]}')
    with pytest.raises(IngestError, match="out of range for EPSG:4326"):
        read_source(p)
    gdf, crs = read_source(p, crs_hint="EPSG:32643")
    assert crs == "EPSG:32643"


def test_csv_without_coordinate_columns_rejected(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("id,name\n1,a\n")
    with pytest.raises(IngestError, match="latitude/longitude"):
        read_source(p)


def test_invalid_geometries_counted(demo_dir):
    assert normalize(read_source(demo_dir / "cadastral.geojson")[0]).invalid_count == 8
