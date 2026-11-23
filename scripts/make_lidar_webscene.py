"""Web scene for the Everglades lidar: point cloud coloured by height over imagery, private.

USE (ArcGIS Pro's Python): "C:/Program Files/ArcGIS/Pro/bin/Python/envs/arcgispro-py3/python.exe" scripts/make_lidar_webscene.py
       <scene-service-item-id> <scene-package-item-id> [<web-scene-item-id to update>]
"""
import json
import sys

from arcgis.gis import GIS

TITLE = "Dosel de manglar en lidar aéreo, río Shark, Everglades"
SNIPPET = "Nube de puntos del lidar aéreo USGS 3DEP (2018) sobre el manglar del río Shark, Everglades, coloreada por altura."
CREDITS = "U.S. Geological Survey, 3D Elevation Program (FL_WestEvergladesNP 2018). Procesado por Lina María Quintero Fonseca."
# height above the ellipsoid-referenced vertical datum of the survey; canopy in this window reaches about 22 m
STOPS = [(-1, [120, 85, 60]), (1, [222, 196, 120]), (5, [150, 205, 110]), (12, [58, 150, 70]), (20, [16, 80, 45])]


def main() -> None:
    gis = GIS("pro")
    layer_item, package_item = gis.content.get(sys.argv[1]), gis.content.get(sys.argv[2])
    for it in (layer_item, package_item):
        it.update({"title": TITLE + (" (paquete)" if it.type == "Scene Package" else ""), "snippet": SNIPPET,
                   "accessInformation": CREDITS, "tags": "lidar, 3DEP, manglar, Everglades, GEDI, nube de puntos"})
    renderer = {"type": "pointCloudStretchRenderer", "field": "ELEVATION", "pointsPerInch": 25,
                "pointSizeAlgorithm": {"type": "pointCloudSplatAlgorithm", "minSize": 2, "scaleFactor": 1},
                "colorModulation": None, "stops": [{"value": v, "color": c + [255]} for v, c in STOPS]}
    scene = {
        "operationalLayers": [{"id": "lidar", "title": "Nube de puntos (altura, m)", "url": layer_item.url + "/layers/0",
                               "itemId": layer_item.id, "layerType": "PointCloudLayer", "visibility": True, "opacity": 1,
                               "layerDefinition": {"drawingInfo": {"renderer": renderer}}}],
        "baseMap": {"title": "Imágenes", "baseMapLayers": [{"id": "imagery", "layerType": "ArcGISTiledMapServiceLayer", "visibility": True,
                                                             "url": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer"}],
                    "elevationLayers": [{"id": "ground", "layerType": "ArcGISTiledElevationServiceLayer", "visibility": True,
                                         "url": "https://elevation3d.arcgis.com/arcgis/rest/services/WorldElevation3D/Terrain3D/ImageServer"}]},
        "ground": {"layers": [{"id": "ground", "layerType": "ArcGISTiledElevationServiceLayer", "visibility": True,
                               "url": "https://elevation3d.arcgis.com/arcgis/rest/services/WorldElevation3D/Terrain3D/ImageServer"}]},
        "initialState": {"viewpoint": {"camera": {"position": {"x": -81.1165, "y": 25.3615, "z": 2200, "spatialReference": {"wkid": 4326}},
                                                  "heading": 0, "tilt": 58}}},
        "spatialReference": {"wkid": 102100, "latestWkid": 3857}, "viewingMode": "global",
        "version": "1.32", "authoringApp": "ArcGIS API for Python", "authoringAppVersion": "2.4",
    }
    if len(sys.argv) > 3:
        ws = gis.content.get(sys.argv[3]); ws.update(item_properties={"text": json.dumps(scene, ensure_ascii=False)})
        print("web scene updated", ws.id); return
    folder = next((f for f in gis.content.folders.list() if f.name == "Everglades lidar"), None) or gis.content.folders.create("Everglades lidar")
    for it in (layer_item, package_item):
        if it.ownerFolder != folder.properties.get("id"):
            it.move(folder)
    ws = folder.add({"type": "Web Scene", "title": TITLE + " (escena)", "snippet": SNIPPET, "accessInformation": CREDITS,
                     "tags": "lidar, 3DEP, manglar, Everglades, GEDI", "text": json.dumps(scene, ensure_ascii=False)}).result()
    print("web scene", ws.id)


if __name__ == "__main__":
    main()
