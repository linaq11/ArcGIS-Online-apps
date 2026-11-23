"""Publish the La Mojana layers to ArcGIS Online with the account ArcGIS Pro is signed in to.

Uploads agol/mojana_inundacion.gdb.zip, publishes it as one hosted feature layer (municipalities,
municipalities by month and the monthly series) and turns on time for the monthly layer.
No password is typed here: GIS("pro") reuses ArcGIS Pro's sign-in.
USE (ArcGIS Pro's Python): "C:/Program Files/ArcGIS/Pro/bin/Python/envs/arcgispro-py3/python.exe" scripts/publish_agol.py [--share public]
"""
import argparse
from pathlib import Path

from arcgis.gis import GIS

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "agol" / "mojana_inundacion.gdb.zip"
TITLE = "Inundación de La Mojana por municipio, Sentinel-1 2020-2025"
NEEDED = ("portal:user:createItem", "portal:publisher:publishFeatures")
DESCRIPTION = ("Área inundada nueva por municipio y por mes en La Mojana (Colombia), de enero de 2020 a diciembre de 2025, "
               "mapeada con radar Sentinel-1 (VV por debajo de −18 dB). Municipios: DANE, MGN 2025. "
               "Método y código: https://github.com/linaq11/ArcGIS-Online-apps")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--share", choices=["private", "org", "public"], default="private")
    a = p.parse_args()
    gis = GIS("pro")
    me = gis.users.me
    missing = [x for x in NEEDED if x not in (me.privileges or [])]
    if missing:
        raise SystemExit(f"This account cannot publish yet; missing privileges: {', '.join(missing)}")
    if not ZIP.exists():
        raise SystemExit(f"Build {ZIP.name} first with scripts/make_fgdb.py")

    folder = next((f for f in gis.content.folders.list() if f.name == "La Mojana"), None) or gis.content.folders.create("La Mojana")
    item = folder.add({"type": "File Geodatabase", "title": TITLE + " (datos)", "tags": "inundación, Sentinel-1, SAR, La Mojana, Colombia"},
                      file=str(ZIP)).result()
    service = item.publish({"name": "mojana_inundacion_municipios"})
    service.update({"title": TITLE, "description": DESCRIPTION, "snippet": "Inundación nueva mensual por municipio, radar Sentinel-1.",
                    "accessInformation": "Lina María Quintero Fonseca. Radar: Copernicus Sentinel-1 (ESA). Municipios: DANE MGN 2025.",
                    "tags": "inundación, Sentinel-1, SAR, La Mojana, Colombia"})

    # time on the monthly layer, one step per month
    monthly = next(l for l in service.layers if l.properties.name == "municipios_mensual")
    monthly.manager.update_definition({"timeInfo": {"startTimeField": "fecha", "endTimeField": None, "trackIdField": "codigo_dane",
                                                    "timeInterval": 1, "timeIntervalUnits": "esriTimeUnitsMonths"}})
    if a.share != "private":
        service.sharing.sharing_level = "EVERYONE" if a.share == "public" else "ORGANIZATION"
    print("published", service.title, service.homepage)
    for l in service.layers + service.tables:
        print(" ", l.properties.name, l.url)


if __name__ == "__main__":
    main()
