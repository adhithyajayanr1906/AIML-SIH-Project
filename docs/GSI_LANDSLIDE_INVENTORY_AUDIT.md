# GSI Landslide Inventory Audit

## 1. Access Investigation
**Target Source:** https://bhusanket.gsi.gov.in/ (Geological Survey of India)

**Findings:** 
The GSI Bhusanket Portal employs a dynamic interactive WebGIS application for hosting the 'Landslide Inventory (Field Validated)'. It heavily relies on client-side JavaScript rendering and session negotiations.

## 2. Access Limitation
Direct programmatic API/HTTP extraction is blocked and returns "Unable to fetch data from the server" without appropriate geographic bounding box payloads, authentication cookies, or explicit browser executions. Automated scraping violates respectful interaction policies and is prevented by design.

## 3. Verified Public Access Method
To legitimately procure this dataset for the project:
1. Open a standard Web Browser and visit `https://bhusanket.gsi.gov.in/`.
2. Locate the Web Map application and activate the **Landslide Inventory (Field Validated)** layer grouping.
3. Utilize the portal's UI tools (often 'Attribute Table' or 'Download Data') to export the geographic feature points.
4. Download the file (preferably `.csv`, `.geojson`, or `.shp`).
5. Save the raw extract directly to `data/hazards/raw/gsi_landslide_inventory_field_validated.[ext]`.

## 4. Current Audit Status
**No data downloaded.** 
Consequently, the data structure, coordinate validity, and exact temporal span are unverified. 

## 5. Supervised ML Status
Because a historical ground-truth target is fundamentally absent, spatial and temporal joins (to rainfall, to road networks, to environmental predictor polygons) cannot be reliably executed. 

**GROUND_TRUTH_STATUS:** NOT VERIFIED
**SUPERVISED_ML_STATUS:** NOT READY
