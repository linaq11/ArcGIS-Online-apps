"""Flooded area by municipality and month in La Mojana (PREREGISTRATION.md).

The flood maps are those of Mojana-flood-SAR (scripts/mojana_series.py), repeated here so this repository
runs on its own. Writes data/municipal_monthly.csv.
USE: python scripts/municipal_flood.py --project my-ee-project
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ee
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BOX = [-75.3, 7.9, -74.3, 9.0]
THRESHOLDS = (-16, -18, -20)


def months(start="2020-01", end="2025-12"):
    return [p.strftime("%Y-%m-01") for p in pd.period_range(start, end, freq="M").to_timestamp()]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True)
    p.add_argument("--jobs", type=int, default=6)
    a = p.parse_args()
    ee.Initialize(project=a.project)
    box = ee.Geometry.Rectangle(BOX)
    col = (ee.ImageCollection("COPERNICUS/S1_GRD").filterBounds(box)
           .filter(ee.Filter.eq("instrumentMode", "IW"))
           .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV")).select("VV"))
    flat = ee.Terrain.slope(ee.Image("USGS/SRTMGL1_003")).lte(5)
    permanent = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").gte(90).unmask(0)
    area = ee.Image.pixelArea().divide(1e6)

    def monthly(m):
        start = ee.Date(m)
        return col.filterDate(start, start.advance(1, "month"))

    ref = {t: ee.ImageCollection([monthly(m).median().lt(t) for m in months("2020-01", "2021-07")]).mean().gte(0.5).unmask(0)
           for t in THRESHOLDS}

    gj = json.loads((ROOT / "data" / "municipios_mgn2025.geojson").read_text(encoding="utf-8"))
    keep = ("MPIO_CDPMP", "MPIO_CNMBRE", "DPTO_CNMBRE")
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"]).intersection(box, 1), {k: f["properties"][k] for k in keep})
                               for f in gj["features"]])

    # area of each municipality inside the box, with the same reducer as the flood
    inside = area.reduceRegions(fc, ee.Reducer.sum().setOutputs(["box_km2"]), 30, tileScale=8).getInfo()   # one band: name the output
    base = {f["properties"]["MPIO_CDPMP"]: f["properties"] for f in inside["features"]}
    for f in gj["features"]:
        base[f["properties"]["MPIO_CDPMP"]]["mpio_km2"] = f["properties"]["MPIO_NAREA"]

    def one(m):
        c = monthly(m)
        n = c.size().getInfo()
        if not n:
            return [{"month": m[:7], "scenes": 0, "MPIO_CDPMP": k} for k in base]
        vv = c.median()
        img = ee.Image.cat([area.updateMask(vv.lt(t).And(flat).And(permanent.Not()).And(ref[t].Not())).rename(f"flood_{-t}")
                            for t in THRESHOLDS])
        res = img.reduceRegions(fc, ee.Reducer.sum(), 30, tileScale=8).getInfo()
        rows = []
        for f in res["features"]:
            q = f["properties"]
            rows.append({"month": m[:7], "scenes": n, "MPIO_CDPMP": q["MPIO_CDPMP"],
                         **{f"flood_{-t}": round(q.get(f"flood_{-t}", 0) or 0, 3) for t in THRESHOLDS}})
        print(m[:7], n, "scenes", flush=True)
        return rows

    with ThreadPoolExecutor(a.jobs) as ex:
        rows = [r for part in ex.map(one, months()) for r in part]
    d = pd.DataFrame(rows)
    d.to_csv(ROOT / "data" / "municipal_monthly_raw.csv", index=False)   # kept in case the join below fails
    meta = pd.DataFrame([{"MPIO_CDPMP": k, "municipio": v["MPIO_CNMBRE"], "departamento": v["DPTO_CNMBRE"],
                          "box_km2": round(v["box_km2"], 2), "share_in_box": round(v["box_km2"] / v["mpio_km2"], 3)}
                         for k, v in base.items()])
    d = d.merge(meta, on="MPIO_CDPMP").sort_values(["month", "MPIO_CDPMP"])
    d["flood_share_18"] = (d["flood_18"] / d["box_km2"]).round(4)
    d.to_csv(ROOT / "data" / "municipal_monthly.csv", index=False)
    print("rows", len(d))


if __name__ == "__main__":
    main()
