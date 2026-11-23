"""GEDI shots of the Everglades lidar comparison as a hosted point layer, and added to the web scene.

Reads lidar-mangrove-canopy/data/gedi_vs_lidar.csv (the 520 shots kept by its preregistered filter), publishes them
as a private hosted feature layer and draws them in the scene at GEDI's RH98 height above the ground, coloured by the
difference with the lidar's 98th percentile in the same footprint.
USE (ArcGIS Pro's Python): "C:/Program Files/ArcGIS/Pro/bin/Python/envs/arcgispro-py3/python.exe" scripts/publish_gedi_shots.py
       <path to gedi_vs_lidar.csv> <web-scene-item-id>
"""
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd
from arcgis.gis import GIS

TITLE = "Disparos GEDI frente a lidar aéreo, río Shark, Everglades"
POWER = {5, 6, 8, 11}                       # GEDI full-power beams; the rest are coverage beams
# GEDI RH98 minus lidar 98th percentile (m): blue when GEDI is lower, red when higher
BREAKS = [(-13, -2, [33, 102, 172]), (-2, -0.5, [146, 197, 222]), (-0.5, 0.5, [247, 247, 247]), (0.5, 2, [244, 165, 130]), (2, 6, [178, 24, 43])]


def main() -> None:
    gis = GIS("pro")
    d = pd.read_csv(sys.argv[1])
    d = d[d.kept]
    feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [float(r.lon), float(r.lat)]}, "properties": {
        "anio": int(r.year), "haz": "potencia" if int(r.beam) in POWER else "cobertura", "sensibilidad": round(float(r.sensitivity), 3),
        "gedi_rh98_m": round(float(r.rh98), 2), "lidar_p98_m": round(float(r.lidar_rh98), 2), "diferencia_m": round(float(r["diff"]), 2)}}
        for _, r in d.iterrows()]
    tmp = Path(tempfile.mkdtemp()) / "gedi_vs_lidar_everglades.geojson"
    tmp.write_text(json.dumps({"type": "FeatureCollection", "features": feats}), encoding="utf-8")
    folder = next(f for f in gis.content.folders.list() if f.name == "Everglades lidar")
    item = folder.add({"type": "GeoJson", "title": TITLE + " (datos)", "tags": "GEDI, lidar, manglar, Everglades"}, file=str(tmp)).result()
    lyr = item.publish()
    lyr.update({"title": TITLE, "snippet": f"{len(feats)} disparos GEDI L2A con la RH98 frente al percentil 98 del lidar 3DEP en la misma huella.",
                "accessInformation": "NASA GEDI L2A; U.S. Geological Survey 3DEP. Procesado por Lina María Quintero Fonseca.",
                "tags": "GEDI, lidar, manglar, Everglades"})
    print("gedi layer", lyr.id, len(feats), "shots")

    renderer = {"type": "classBreaks", "field": "diferencia_m", "minValue": -13,
                "classBreakInfos": [{"classMinValue": lo, "classMaxValue": hi, "label": f"{lo} a {hi} m",
                                     "symbol": {"type": "PointSymbol3D", "symbolLayers": [{"type": "Icon", "size": 9, "resource": {"primitive": "circle"},
                                                "material": {"color": c + [255]}, "outline": {"color": [30, 30, 30, 200], "size": 0.6}}]}}
                                    for lo, hi, c in BREAKS]}
    popup = {"title": "Disparo GEDI, {anio}", "popupElements": [{"type": "fields", "fieldInfos": [
        {"fieldName": "gedi_rh98_m", "label": "GEDI RH98 (m)"}, {"fieldName": "lidar_p98_m", "label": "Lidar, percentil 98 en la huella (m)"},
        {"fieldName": "diferencia_m", "label": "GEDI menos lidar (m)"}, {"fieldName": "haz", "label": "Haz"},
        {"fieldName": "sensibilidad", "label": "Sensibilidad del haz"}]}]}
    ws = gis.content.get(sys.argv[2])
    scene = ws.get_data()
    scene["operationalLayers"] = [l for l in scene["operationalLayers"] if l.get("id") != "gedi"]
    scene["operationalLayers"].append({
        "id": "gedi", "title": "Disparos GEDI: RH98 menos lidar (m)", "url": lyr.layers[0].url, "itemId": lyr.id,
        "layerType": "ArcGISFeatureLayer", "visibility": True, "opacity": 1, "popupInfo": popup,
        # each shot floats at GEDI's RH98 above the ground, so it can be read against the canopy below
        "elevationInfo": {"mode": "relativeToGround", "featureExpressionInfo": {"expression": "$feature.gedi_rh98_m"}, "unit": "meters"},
        "layerDefinition": {"drawingInfo": {"renderer": renderer}}})
    ws.update(item_properties={"text": json.dumps(scene, ensure_ascii=False)})
    print("web scene updated", ws.id)


if __name__ == "__main__":
    main()
