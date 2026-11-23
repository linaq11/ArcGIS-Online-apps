"""Layers for ArcGIS Online from data/municipal_monthly.csv and the DANE municipalities.

Writes to agol/:
  mojana_municipios.geojson          one feature per municipality, with peak and before/after figures
  mojana_municipios_mensual.geojson  one feature per municipality and month, with a date field (time-enabled layer)
  mojana_serie_mensual.csv           box totals per month (chart table)
USE: python scripts/build_layers.py
"""
import json
from pathlib import Path

import pandas as pd
from shapely import set_precision
from shapely.geometry import mapping, shape

ROOT = Path(__file__).resolve().parents[1]
SMALL = {"de", "del", "la", "las", "los", "y"}


def nombre(s: str) -> str:
    """DANE writes names in capitals: 'SAN JACINTO DEL CAUCA' -> 'San Jacinto del Cauca'."""
    w = s.lower().split()
    return " ".join(x if (i and x in SMALL) else x.capitalize() for i, x in enumerate(w))
SIMPLIFY = 0.003          # degrees, about 330 m, for the monthly layer (2,000+ copies of each outline)


def main() -> None:
    d = pd.read_csv(ROOT / "data" / "municipal_monthly.csv", dtype={"MPIO_CDPMP": str})
    gj = json.loads((ROOT / "data" / "municipios_mgn2025.geojson").read_text(encoding="utf-8"))
    geom = {f["properties"]["MPIO_CDPMP"]: shape(f["geometry"]) for f in gj["features"]}
    out = ROOT / "agol"
    out.mkdir(exist_ok=True)
    d = d[d.box_km2 > 0]          # El Roble (Sucre) only touches the edge of the box: no area inside
    ok = d[d.scenes > 0]

    # one feature per municipality
    feats = []
    for k, g in ok.groupby("MPIO_CDPMP"):
        pre = g[g.month < "2021-08"]
        peak = g.loc[g.flood_18.idxmax()]
        dec22 = g[g.month == "2022-12"].flood_18.sum()
        after = g[g.month.isin(["2024-03", "2024-04"])].flood_18.mean()
        feats.append({"type": "Feature", "geometry": mapping(geom[k]), "properties": {
            "codigo_dane": k, "municipio": nombre(g.municipio.iloc[0]), "departamento": nombre(g.departamento.iloc[0]),
            "km2_en_area": float(g.box_km2.iloc[0]), "fraccion_en_area": min(1.0, float(g.share_in_box.iloc[0])),   # pixel areas and DANE's area differ by up to 0.1%
            "inund_max_antes_km2": round(float(pre.flood_18.max()), 2), "inund_dic2022_km2": round(float(dec22), 2),
            "inund_mar_abr2024_km2": round(float(after), 2), "inund_max_km2": round(float(peak.flood_18), 2),
            "mes_max": peak.month}})
    (out / "mojana_municipios.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False), encoding="utf-8")

    # one feature per municipality and month (time-enabled)
    simple = {k: mapping(set_precision(g.simplify(SIMPLIFY, preserve_topology=True), 1e-5)) for k, g in geom.items()}
    feats = [{"type": "Feature", "geometry": simple[r.MPIO_CDPMP], "properties": {
        "codigo_dane": r.MPIO_CDPMP, "municipio": nombre(r.municipio), "departamento": nombre(r.departamento),
        "fecha": f"{r.month}-15", "inund_km2": round(float(r.flood_18), 2), "inund_pct": round(100 * float(r.flood_share_18), 2),
        "inund_16_km2": round(float(r.flood_16), 2), "inund_20_km2": round(float(r.flood_20), 2)}}
        for r in ok.itertuples()]
    (out / "mojana_municipios_mensual.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False), encoding="utf-8")

    # monthly totals for charts
    s = d.groupby("month").agg(escenas=("scenes", "first"), inund_km2=("flood_18", "sum"),
                               inund_16_km2=("flood_16", "sum"), inund_20_km2=("flood_20", "sum")).reset_index()
    s.loc[s.escenas == 0, ["inund_km2", "inund_16_km2", "inund_20_km2"]] = None
    s.insert(1, "fecha", s.month + "-15")
    s.round(2).to_csv(out / "mojana_serie_mensual.csv", index=False)
    for f in out.iterdir():
        print(f.name, f.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
