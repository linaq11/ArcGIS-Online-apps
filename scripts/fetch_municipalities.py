"""Municipalities of DANE's Marco Geoestadístico Nacional 2025 that touch the La Mojana box (PREREGISTRATION.md).

Queries the public DANE service and writes data/municipios_mgn2025.geojson (WGS 84).
USE: python scripts/fetch_municipalities.py
"""
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BOX = [-75.3, 7.9, -74.3, 9.0]
URL = "https://portalgis.dane.gov.co/mparcgis/rest/services/Divipola/Serv_DIVIPOLA_MGN_2025/FeatureServer/317/query"


def main() -> None:
    r = requests.get(URL, timeout=120, params={
        "geometry": ",".join(map(str, BOX)), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects", "outFields": "DPTO_CCDGO,MPIO_CDPMP,DPTO_CNMBRE,MPIO_CNMBRE,MPIO_NAREA",
        "outSR": 4326, "maxAllowableOffset": 0.0002, "geometryPrecision": 6, "f": "geojson"})
    r.raise_for_status()
    fc = r.json()
    if fc.get("error") or not fc.get("features"):
        raise SystemExit(f"DANE service returned no features: {str(fc)[:300]}")
    out = ROOT / "data"
    out.mkdir(exist_ok=True)
    (out / "municipios_mgn2025.geojson").write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    names = sorted(f"{f['properties']['MPIO_CNMBRE']} ({f['properties']['DPTO_CNMBRE']})" for f in fc["features"])
    print(len(names), "municipalities:", "; ".join(names))


if __name__ == "__main__":
    main()
