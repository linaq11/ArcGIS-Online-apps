"""Web map for the La Mojana app: flooded area by municipality and month, time slider, Arcade pop-ups.

Writes the web map JSON directly (operational layers, class-breaks renderer, pop-ups, time slider) and adds it as a
private item next to the hosted layer published by scripts/publish_agol.py.
USE (ArcGIS Pro's Python): "C:/Program Files/ArcGIS/Pro/bin/Python/envs/arcgispro-py3/python.exe" scripts/make_webmap.py <feature-service-item-id> [<web-map-item-id to update>]
"""
import json
import sys

from arcgis.gis import GIS

TITLE = "Inundación de La Mojana por municipio, 2020-2025 (mapa)"
START, FEB2020, END = 1577836800000, 1580515200000, 1767225600000      # 2020-01-01, 2020-02-01 and 2026-01-01, UTC
# new flood (km2) in a municipality and month; breaks near the 50th, 75th, 90th and 95th percentiles of the data
# water colours, light to deep blue; (lower, upper, RGB, alpha 0-255): almost clear when there is no new flood
BREAKS = [(0, 1, [198, 233, 245], 25), (1, 10, [127, 205, 234], 110), (10, 50, [58, 155, 213], 140), (50, 150, [31, 98, 179], 165), (150, 400, [11, 47, 107], 185)]

POPUP_MONTHLY = {
    "title": "{municipio}, {departamento}",
    "expressionInfos": [
        {"name": "mes", "title": "Mes", "expression": "Text($feature.fecha, 'MMMM Y')", "returnType": "string"},
        {"name": "resumen", "title": "Inundación nueva", "returnType": "string",
         "expression": "var km = $feature.inund_km2; var pct = $feature.inund_pct;\n"
                       "return Text(km, '#,##0.0') + ' km² de inundación nueva, ' + Text(pct, '0.0') + ' % del municipio dentro del área de estudio';"},
        {"name": "umbral", "title": "Sensibilidad al umbral", "returnType": "string",
         "expression": "'Entre ' + Text($feature.inund_20_km2, '#,##0.0') + ' km² (−20 dB) y ' + Text($feature.inund_16_km2, '#,##0.0') + ' km² (−16 dB)'"},
    ],
    "popupElements": [
        {"type": "text", "text": "<b>{expression/mes}</b><br>{expression/resumen}<br><span style='color:#777'>{expression/umbral}</span>"},
    ],
}

POPUP_STATIC = {
    "title": "{municipio}, {departamento}",
    "expressionInfos": [
        {"name": "cambio", "title": "Pico frente a antes", "returnType": "string",
         "expression": "var antes = $feature.inund_max_antes_km2; var pico = $feature.inund_dic2022_km2;\n"
                       "if (antes < 0.5) { return 'Sin inundación nueva apreciable antes de la ruptura'; }\n"
                       "return 'Diciembre de 2022: ' + Text(pico / antes, '0.0') + ' veces el mes más alto antes de la ruptura';"},
    ],
    "popupElements": [
        {"type": "fields", "fieldInfos": [
            {"fieldName": "inund_max_antes_km2", "label": "Mes más alto antes de la ruptura (km²)", "format": {"places": 1, "digitSeparator": True}},
            {"fieldName": "inund_dic2022_km2", "label": "Diciembre de 2022, el pico regional (km²)", "format": {"places": 1, "digitSeparator": True}},
            {"fieldName": "inund_mar_abr2024_km2", "label": "Marzo y abril de 2024, tras el cierre (km²)", "format": {"places": 1, "digitSeparator": True}},
            {"fieldName": "fraccion_en_area", "label": "Fracción del municipio dentro del área de estudio", "format": {"places": 2}}]},
        {"type": "text", "text": "{expression/cambio}"},
    ],
}


def main() -> None:
    gis = GIS("pro")
    svc = gis.content.get(sys.argv[1])
    url = {l.properties.name: l.url for l in svc.layers}
    renderer = {"type": "classBreaks", "field": "inund_km2", "minValue": 0,
                "classBreakInfos": [{"classMinValue": lo, "classMaxValue": hi, "label": f"{lo} a {hi} km²",
                                     "symbol": {"type": "esriSFS", "style": "esriSFSSolid", "color": c + [a],
                                                "outline": {"type": "esriSLS", "style": "esriSLSSolid", "color": [255, 255, 255, 0], "width": 0}}}
                                    for lo, hi, c, a in BREAKS]}
    webmap = {
        "operationalLayers": [
            {"id": "mensual", "title": "Inundación nueva por mes (km²)", "url": url["municipios_mensual"], "layerType": "ArcGISFeatureLayer",
             "visibility": True, "opacity": 1, "layerDefinition": {"drawingInfo": {"renderer": renderer}}, "popupInfo": POPUP_MONTHLY},
            {"id": "municipios", "title": "Municipios (DANE, MGN 2025)", "url": url["municipios"], "layerType": "ArcGISFeatureLayer",
             "visibility": True, "opacity": 1, "popupInfo": POPUP_STATIC,
             "layerDefinition": {"drawingInfo": {
                 "renderer": {"type": "simple", "symbol": {"type": "esriSFS", "style": "esriSFSNull",
                                                           "outline": {"type": "esriSLS", "style": "esriSLSSolid", "color": [255, 255, 255, 170], "width": 0.6}}},
                 "labelingInfo": [{"labelExpressionInfo": {"expression": "$feature.municipio"}, "labelPlacement": "esriServerPolygonPlacementAlwaysHorizontal",
                                   "symbol": {"type": "esriTS", "color": [255, 255, 255, 235], "haloColor": [10, 30, 50, 150], "haloSize": 0.8,
                                              "font": {"family": "Arial", "size": 8, "weight": "normal"}}}],
                 "showLabels": True}}},
        ],
        "baseMap": {"title": "Imágenes", "baseMapLayers": [{"id": "imagery", "layerType": "ArcGISTiledMapServiceLayer", "visibility": True, "opacity": 1,
                                                             "url": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer"}]},
        "initialState": {"viewpoint": {"targetGeometry": {"xmin": -75.3, "ymin": 7.9, "xmax": -74.3, "ymax": 9.0, "spatialReference": {"wkid": 4326}}}},
        "spatialReference": {"wkid": 102100, "latestWkid": 3857},
        # a one-month window that steps month by month, so each stop shows a single month (features are dated on the 15th)
        "widgets": {"timeSlider": {"properties": {"startTime": START, "endTime": END, "currentTimeExtent": [START, FEB2020],
                                                  "thumbCount": 2, "thumbMovingRate": 1500,
                                                  "timeStopInterval": {"interval": 1, "units": "esriTimeUnitsMonths"}}}},
        "version": "2.31", "authoringApp": "ArcGIS API for Python", "authoringAppVersion": "2.4",
    }
    if len(sys.argv) > 2:                     # update an existing web map item instead of adding a new one
        item = gis.content.get(sys.argv[2]); item.update(item_properties={"text": json.dumps(webmap, ensure_ascii=False)})
        print("web map updated", item.id, item.homepage); return
    folder = next(f for f in gis.content.folders.list() if f.name == "La Mojana")
    item = folder.add({"type": "Web Map", "title": TITLE, "tags": "inundación, Sentinel-1, La Mojana, Colombia",
                       "snippet": "Inundación nueva por municipio y por mes, radar Sentinel-1, 2020-2025.",
                       "text": json.dumps(webmap, ensure_ascii=False)}).result()
    print("web map", item.id, item.homepage)


if __name__ == "__main__":
    main()
