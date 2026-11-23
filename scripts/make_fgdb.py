"""File geodatabase for ArcGIS Online, built with arcpy from the files in agol/.

Real date fields (the time slider needs them) and Spanish field aliases for pop-ups and charts.
Writes agol/mojana_inundacion.gdb and agol/mojana_inundacion.gdb.zip.
USE (ArcGIS Pro's Python): "C:/Program Files/ArcGIS/Pro/bin/Python/envs/arcgispro-py3/python.exe" scripts/make_fgdb.py
"""
import shutil
import zipfile
from pathlib import Path

import arcpy

ROOT = Path(__file__).resolve().parents[1]
AG = ROOT / "agol"
GDB = AG / "mojana_inundacion.gdb"

ALIASES = {
    "codigo_dane": "Código DANE", "municipio": "Municipio", "departamento": "Departamento",
    "km2_en_area": "Área del municipio dentro del área de estudio (km²)", "fraccion_en_area": "Fracción del municipio dentro del área de estudio",
    "inund_max_antes_km2": "Inundación nueva, mes más alto antes de la ruptura (km²)", "inund_dic2022_km2": "Inundación nueva, diciembre de 2022 (km²)",
    "inund_mar_abr2024_km2": "Inundación nueva, media de marzo y abril de 2024 (km²)", "inund_max_km2": "Inundación nueva, mes más alto (km²)",
    "mes_max": "Mes más alto", "fecha": "Mes", "inund_km2": "Inundación nueva (km²)", "inund_pct": "Inundación nueva (% del área)",
    "inund_16_km2": "Inundación nueva con −16 dB (km²)", "inund_20_km2": "Inundación nueva con −20 dB (km²)", "escenas": "Escenas Sentinel-1",
}


def to_date(table: str) -> None:
    """Replace the text field 'fecha' (YYYY-MM-DD) by a date field with the same name."""
    arcpy.management.AddField(table, "fecha_d", "DATE")
    arcpy.management.CalculateField(table, "fecha_d", "None if not !fecha! else datetime.datetime.strptime(!fecha!, '%Y-%m-%d')", "PYTHON3")
    arcpy.management.DeleteField(table, "fecha")
    arcpy.management.AlterField(table, "fecha_d", "fecha", ALIASES["fecha"])


def aliases(table: str) -> None:
    for f in arcpy.ListFields(table):
        if f.name in ALIASES and f.aliasName != ALIASES[f.name]:
            arcpy.management.AlterField(table, f.name, new_field_alias=ALIASES[f.name])


def main() -> None:
    shutil.rmtree(GDB, ignore_errors=True)
    arcpy.management.CreateFileGDB(str(AG), GDB.name)
    arcpy.env.overwriteOutput = True
    municipios = str(GDB / "municipios")
    mensual = str(GDB / "municipios_mensual")
    serie = str(GDB / "serie_mensual")
    arcpy.conversion.JSONToFeatures(str(AG / "mojana_municipios.geojson"), municipios, "POLYGON")
    arcpy.conversion.JSONToFeatures(str(AG / "mojana_municipios_mensual.geojson"), mensual, "POLYGON")
    arcpy.conversion.ExportTable(str(AG / "mojana_serie_mensual.csv"), serie)
    to_date(mensual)
    to_date(serie)
    for t in (municipios, mensual, serie):
        aliases(t)
        print(t, arcpy.management.GetCount(t)[0], "rows", [f"{f.name}:{f.type}" for f in arcpy.ListFields(t)][:12])
    arcpy.management.ClearWorkspaceCache()
    zipped = AG / (GDB.name + ".zip")
    with zipfile.ZipFile(zipped, "w", zipfile.ZIP_DEFLATED) as z:
        for f in GDB.iterdir():
            if not f.name.endswith(".lock"):   # lock files belong to this session, not to the data
                z.write(f, f"{GDB.name}/{f.name}")
    print("zip", zipped, zipped.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
