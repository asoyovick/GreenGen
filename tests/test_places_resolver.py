"""Basic gazetteer/search/resolver tests using synthetic fixtures."""
from __future__ import annotations

import json

from src.places.gazetteer import (
    Gazetteer,
    build_city_records,
    build_country_records,
    build_region_records,
    build_sea_records,
    finalize_record,
)


def _fc(features):
    return {"type": "FeatureCollection", "features": features}


def build_fixture_gazetteer(tmp_path):
    countries = tmp_path / "countries.geojson"
    regions = tmp_path / "regions.geojson"
    cities = tmp_path / "cities.geojson"
    seas = tmp_path / "seas.geojson"

    kenya = {
        "type": "Feature",
        "properties": {"NAME_EN": "Kenya", "NAME": "Kenya", "ADM0_A3": "KEN", "ISO_A3": "KEN", "NE_ID": 1},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[33.5, -5.0], [42.2, -5.0], [42.2, 5.2], [33.5, 5.2], [33.5, -5.0]]],
        },
    }
    fiji = {
        "type": "Feature",
        "properties": {"NAME_EN": "Fiji", "NAME": "Fiji", "ADM0_A3": "FJI", "ISO_A3": "FJI", "NE_ID": 2},
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [
                [[[176.8, -19.2], [179.9, -19.2], [179.9, -16.0], [176.8, -16.0], [176.8, -19.2]]],
                [[[-179.9, -19.2], [-178.0, -19.2], [-178.0, -16.0], [-179.9, -16.0], [-179.9, -19.2]]],
            ],
        },
    }
    countries.write_text(json.dumps(_fc([kenya, fiji])))
    nairobi_county = {
        "type": "Feature",
        "properties": {"name_en": "Nairobi County", "name": "Nairobi", "adm0_a3": "KEN", "adm1_code": "KEN-1", "ne_id": 10},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[36.6, -1.45], [37.1, -1.45], [37.1, -1.15], [36.6, -1.15], [36.6, -1.45]]],
        },
    }
    regions.write_text(json.dumps(_fc([nairobi_county])))
    nairobi = {
        "type": "Feature",
        "properties": {"name": "Nairobi", "adm0_a3": "KEN", "adm1name": "Nairobi County", "ne_id": 100, "pop_max": 2750547},
        "geometry": {"type": "Point", "coordinates": [36.8167, -1.2833]},
    }
    cities.write_text(json.dumps(_fc([nairobi])))
    pacific = {
        "type": "Feature",
        "properties": {"name_en": "Pacific Ocean", "name": "Pacific Ocean", "ne_id": 200, "featurecla": "ocean"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[-170, -10], [-140, -10], [-140, 10], [-170, 10], [-170, -10]]],
        },
    }
    seas.write_text(json.dumps(_fc([pacific])))

    country_recs = build_country_records(countries)
    region_recs = build_region_records(regions, country_recs)
    city_recs = build_city_records(cities, country_recs, region_recs)
    sea_recs = build_sea_records(seas)
    places = []
    for items in (country_recs, region_recs, city_recs, sea_recs):
        for rec, geom in items:
            places.append(finalize_record(rec, geom, simplify_display=0.0, simplify_mask=0.0)[0])
    return Gazetteer(places)


def test_resolve_country_and_region(tmp_path):
    gaz = build_fixture_gazetteer(tmp_path)
    country = gaz.resolve(-1.286, 36.817, "country")
    assert country["place"]["name"] == "Kenya"
    region = gaz.resolve(-1.286, 36.817, "region")
    assert region["place"]["name"] == "Nairobi County"
    assert "Kenya" in region["place"]["hierarchy"]


def test_resolve_city_nearest(tmp_path):
    gaz = build_fixture_gazetteer(tmp_path)
    city = gaz.resolve(-1.29, 36.82, "city")
    assert city["place"]["name"] == "Nairobi"
    assert "Nairobi County" in city["place"]["hierarchy"] or "Kenya" in city["place"]["hierarchy"]


def test_resolve_open_ocean(tmp_path):
    gaz = build_fixture_gazetteer(tmp_path)
    sea = gaz.resolve(0.0, -150.0, "sea")
    assert sea["place"]["name"] == "Pacific Ocean"
    far = gaz.resolve(0.0, 0.0, "sea")
    assert far.get("place") is None
    assert far.get("open_ocean") is True


def test_search_case_diacritic_and_hierarchy(tmp_path):
    gaz = build_fixture_gazetteer(tmp_path)
    res = gaz.search("nairobi")
    assert res
    assert any(r["name"] == "Nairobi" for r in res)
    # hierarchy shown in results
    assert any("Kenya" in r["hierarchy"] for r in res)


def test_antimeridian_country_resolution(tmp_path):
    gaz = build_fixture_gazetteer(tmp_path)
    # point in Fiji's eastern (negative lon) polygon part
    res = gaz.resolve(-17.8, -179.2, "country")
    assert res["place"]["name"] == "Fiji"
