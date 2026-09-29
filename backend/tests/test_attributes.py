import pandas as pd

from app.engine.attributes import apply_mapping, map_fields, name_similarity

REVENUE = pd.DataFrame({"Khasra_No": ["KH-104"], "Owner_Name": ["Rahul Sharma"], "Land_Area": [420.0],
                        "Land_Type": ["RESIDENTIAL"]})
MUNICIPAL = pd.DataFrame({"Property_ID": ["M7781"], "Owner": ["R. Sharma"], "Area": [418.2], "Usage": ["Residential"]})


def as_dict(ms):
    return {m.source_field: m.canonical_field for m in ms}


def test_prd_revenue_mapping():
    assert as_dict(map_fields(REVENUE)) == {"Khasra_No": "parcel_id", "Owner_Name": "owner_name",
                                            "Land_Area": "area", "Land_Type": "land_use"}


def test_prd_municipal_mapping():
    assert as_dict(map_fields(MUNICIPAL)) == {"Property_ID": "source_property_id", "Owner": "owner_name",
                                              "Area": "area", "Usage": "land_use"}


def test_synonym_confidence_high():
    assert all(m.confidence >= 0.9 and m.method == "synonym" for m in map_fields(MUNICIPAL))


def test_fuzzy_field_name_maps_with_lower_confidence():
    m = map_fields(pd.DataFrame({"OwnrName": ["A B"]}))[0]
    assert m.canonical_field == "owner_name" and m.method == "fuzzy" and m.confidence < 0.95


def test_unknown_field_unmapped():
    m = map_fields(pd.DataFrame({"zzz_flag": [1]}))[0]
    assert m.canonical_field is None and m.method == "unmapped"


def test_geometry_and_coordinate_columns_skipped():
    ms = map_fields(pd.DataFrame({"latitude": [1.0], "geometry": [None], "Owner": ["A B"]}))
    assert [m.source_field for m in ms] == ["Owner"]


def test_name_similarity():
    assert name_similarity("Rahul Sharma", "SHARMA RAHUL") == 1.0
    assert name_similarity("Rahul Sharma", "R. Sharma") >= 0.8
    assert name_similarity("Rahul Sharma", "Priya Deshmukh") < 0.5
    assert name_similarity("Rahul Sharma", None) is None


def test_apply_mapping_normalizes_values():
    out = apply_mapping(REVENUE, map_fields(REVENUE))
    assert out.loc[0, "land_use"] == "Residential" and out.loc[0, "area"] == 420.0
    assert out.loc[0, "parcel_id"] == "KH-104"


def test_apply_mapping_missing_values_are_none():
    df = pd.DataFrame({"Owner": [None, "  Rahul   Sharma "], "Usage": ["MIXED USE", float("nan")]})
    out = apply_mapping(df, map_fields(df))
    assert out.loc[0, "owner_name"] is None and out.loc[1, "owner_name"] == "Rahul Sharma"
    assert out.loc[0, "land_use"] == "Mixed Use" and out.loc[1, "land_use"] is None
