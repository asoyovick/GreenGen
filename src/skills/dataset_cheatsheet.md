# Dataset cheatsheet

**Verify every row in Earthdata Search and by opening one file.** Names, versions, and variable names change; this table is a starting point.

| Variable | Search for (short name) | Surface | DAAC | Resolution | Format | Check |
|---|---|---|---|---|---|---|
| Precipitation | `GPM_3IMERGM` (IMERG monthly) | Land, ocean | GES DISC | 0.1° | NetCDF4/HDF5 | Units are a rate (mm/hr); multiply by hours in month. Lower reliability at high latitudes |
| Vegetation greenness | `MOD13C2` (MODIS Terra monthly, climate-modeling grid) | Land | LP DAAC | 0.05° | HDF4 | Scale factor 0.0001; HDF4 handling |
| Land surface temperature | `MOD11C3` (MODIS Terra monthly CMG) | Land | LP DAAC | 0.05° | HDF4 | Scale factor 0.02 gives Kelvin; cloud gaps |
| Air temperature, humidity | `M2TMNXSLV` (MERRA-2 monthly single level) | Global | GES DISC | 0.5° x 0.625° | NetCDF4 | `T2M` in Kelvin; model-produced, gap-free |
| Terrestrial water storage | search "GRACE mascon" | Land | PO.DAAC | 0.5° grid, effective hundreds of km | NetCDF | Liquid water equivalent thickness (cm); 2017-2018 gap; longitudes 0 to 360 |
| Sea ice concentration | search `NSIDC-0051` | Polar oceans | NSIDC | 25 km | NetCDF/binary | Polar projection; reprojection may be needed |
| Soil moisture (model) | `GLDAS_NOAH025_M` | Land | GES DISC | 0.25° | NetCDF4 | Several soil layers; choose and document one |
| Soil moisture (satellite) | search "SMAP L3 soil moisture" | Land | NSIDC | 9 to 36 km | HDF5 | Record since 2015: low trend reliability |
| Night lights | `VNP46A3` (VIIRS Black Marble monthly) | Land | LAADS | 500 m tiles | HDF5 | Record since 2012; tiled |
| Sea surface temperature | GHRSST products (for example MUR) | Ocean | PO.DAAC | 1 to 25 km | NetCDF | Very large; use monthly or coarsened |

## Archive centers

GES DISC disc.gsfc.nasa.gov · LP DAAC lpdaac.usgs.gov · PO.DAAC podaac.jpl.nasa.gov · NSIDC nsidc.org · OB.DAAC oceancolor.gsfc.nasa.gov · LAADS ladsweb.modaps.eosdis.nasa.gov

## Config entry template

```yaml
imerg_precip:
  short_name: GPM_3IMERGM
  version: "07"
  variable: precipitation
  units_in: mm/hr
  units_out: mm/month
  surface: [land, ocean]
  period: [2002-01, 2024-12]
  native_resolution_deg: 0.1
  notes: "Multiply by hours in month. Check high-latitude quality."
```
