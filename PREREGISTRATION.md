# Preregistration: flooded area by municipality in La Mojana

Written on 2026-11-20, before any municipal figure was computed.

## Question

How was the new flood water mapped by Sentinel-1 in La Mojana shared among municipalities before the Cara de Gato dike broke (January 2020 to July 2021), at the peak (December 2022) and after the closure (March and April 2024)?

## Data, fixed in advance

* **Flood.** The monthly flood maps of [Mojana-flood-SAR](https://github.com/linaq11/Mojana-flood-SAR), unchanged: VV below −18 dB in the monthly Sentinel-1 median, slope of 5° or less, not permanent water (JRC occurrence of 90% or more), and not water in at least half of the months from January 2020 to July 2021. The −16 and −20 dB versions are kept as a sensitivity check.
* **Municipalities.** DANE, Marco Geoestadístico Nacional 2025, layer Municipio of the service `Divipola/Serv_DIVIPOLA_MGN_2025`, every municipality that touches the box 75.3° W to 74.3° W, 7.9° N to 9.0° N.
* **Area.** Only the part of each municipality inside that box is counted, and the share of the municipality inside the box is reported next to it.

## Method

For each month and municipality, the flooded area is the sum of the Earth Engine pixel areas of flood cells inside the municipality and the box, at 30 m, with the same reducer as the monthly series. The flooded share is that area over the municipality's area inside the box.

## Expectation, stated before computing

At the December 2022 peak, more than half of the new flood area lies in four municipalities on the left bank of the Cauca downstream of the breach: Guaranda, Majagual and Sucre (department of Sucre) and San Jacinto del Cauca (Bolívar).

## Check

The municipal areas of each month must add up to the box total of `data/mojana_monthly.csv` in Mojana-flood-SAR within 1%. If they do not, the municipal figures are not reported until the difference is explained.

## What is reported

All municipalities and all months, including disagreement with the expectation. The figures are published as ArcGIS Online hosted layers and shown in an Experience Builder app.
