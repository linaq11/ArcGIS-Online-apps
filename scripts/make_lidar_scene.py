"""Everglades lidar as an ArcGIS Online point cloud scene layer (second app of this repository).

1. LAS dataset over the UTM 17N tiles written by lidar-mangrove-canopy/scripts/export_scene_tiles.py.
2. Point cloud scene layer package (.slpk) in WGS 84 without the noise classes (7 and 18), keeping intensity,
   classification and returns.
3. Upload and publish to ArcGIS Online, private; sharing is a separate, explicit step.
No password is typed here: GIS("pro") reuses ArcGIS Pro's sign-in.
USE (ArcGIS Pro's Python): "C:/Program Files/ArcGIS/Pro/bin/Python/envs/arcgispro-py3/python.exe" scripts/make_lidar_scene.py
       --tiles D:/LIDAR_3DEP_Everglades/scene_laz --work D:/LIDAR_3DEP_Everglades/scene_pkg
"""
import argparse
from pathlib import Path

import arcpy
from arcgis.gis import GIS

TITLE = "Dosel de manglar en lidar aéreo, río Shark, Everglades (nube de puntos)"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--tiles", required=True, type=Path)
    p.add_argument("--work", required=True, type=Path)
    p.add_argument("--skip-package", action="store_true")
    a = p.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("3D")
    lasd = a.work / "everglades_window.lasd"
    slpk = a.work / "everglades_window.slpk"
    if not a.skip_package:
        arcpy.management.CreateLasDataset([str(f) for f in sorted(a.tiles.glob("*.laz"))], str(lasd),
                                          spatial_reference=arcpy.SpatialReference(32617), compute_stats="COMPUTE_STATS")
        # noise classes out: 7 (low noise) and 18 (high noise, up to 530 m) would draw as false spikes
        lyr = arcpy.management.MakeLasDatasetLayer(str(lasd), "everglades_sin_ruido", class_code=[1, 2, 8, 9, 13]).getOutput(0)
        arcpy.management.CreatePointCloudSceneLayerPackage(
            lyr, str(slpk), arcpy.SpatialReference(4326),
            attributes=["INTENSITY", "RETURNS", "CLASS_CODE", "FLAGS"], scene_layer_version="2.x")
        print("slpk", slpk, round(slpk.stat().st_size / 1e6), "MB")
    gis = GIS("pro")
    folder = next((f for f in gis.content.folders.list() if f.name == "Everglades lidar"), None) or gis.content.folders.create("Everglades lidar")
    item = folder.add({"type": "Scene Package", "title": TITLE + " (paquete)", "tags": "lidar, 3DEP, manglar, Everglades, GEDI"},
                      file=str(slpk)).result()
    scene = item.publish()
    scene.update({"title": TITLE, "snippet": "Nube de puntos del lidar aéreo USGS 3DEP (2018) sobre el manglar del río Shark, Everglades.",
                  "accessInformation": "U.S. Geological Survey, 3D Elevation Program (FL_WestEvergladesNP 2018). Procesado por Lina María Quintero Fonseca.",
                  "tags": "lidar, 3DEP, manglar, Everglades, GEDI"})
    print("scene layer", scene.id, scene.homepage, scene.url)


if __name__ == "__main__":
    main()
