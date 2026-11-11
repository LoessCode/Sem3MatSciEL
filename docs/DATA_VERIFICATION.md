# Data verification checklist

**Every value in `data/materials.json` is a typical figure from general engineering knowledge, given as a min-max range, and every record carries the status `typical-value-needs-verification`.**
Before the project is submitted or any result is relied on, spot-check the values below against supplier datasheets or an engineering handbook (cite the source you actually used in your report), tick the box, and note the source in the last column.

How to use this file:

1. Pick the highest-impact materials first: the top-ranked materials in your demo scenarios and the ones you intend to defend.
2. For each property, check that the stated range brackets the datasheet value for the grade and process you mean (for example XY-printed filament, quasi-isotropic laminate at about 50% fibre volume).
3. If a value is wrong, edit `data/materials.json`, run `python scripts/validate_data.py` and `make test`, and re-run `python scripts/make_validation_report.py`.
4. Change `data_status` to a verified status only for records you have fully checked, and extend the validator accordingly.

Scores (impact resistance, recyclability) are 1-5 judgement values; review them with your instructor rather than a datasheet.

Legend: `[ ]` = not yet verified. Ranges are shown as min-max.

| Material (id) | Family | Density kg/m3 | E GPa | Strength MPa | Tmax C | Cost $/kg | Emb. energy MJ/kg | Impact 1-5 | Recycl. 1-5 | Source / notes |
|---|---|---|---|---|---|---|---|---|---|---|
| PLA (`pla`) | printable-polymer | 1200-1270 [ ] | 2.3-3.5 [ ] | 40-60 [ ] | 50-60 [ ] | 15-30 [ ] | 40-60 [ ] | 1 [ ] | 2 [ ] |  |
| PLA+ (toughened PLA) (`pla-plus`) | printable-polymer | 1210-1270 [ ] | 2-3 [ ] | 45-65 [ ] | 55-60 [ ] | 18-35 [ ] | 45-65 [ ] | 2 [ ] | 2 [ ] |  |
| PETG (`petg`) | printable-polymer | 1260-1290 [ ] | 1.8-2.5 [ ] | 40-55 [ ] | 65-75 [ ] | 18-32 [ ] | 75-95 [ ] | 3 [ ] | 3 [ ] |  |
| ABS (`abs`) | printable-polymer | 1030-1070 [ ] | 1.6-2.4 [ ] | 30-45 [ ] | 85-100 [ ] | 18-30 [ ] | 90-110 [ ] | 3 [ ] | 3 [ ] |  |
| ASA (`asa`) | printable-polymer | 1050-1090 [ ] | 1.8-2.4 [ ] | 30-45 [ ] | 85-95 [ ] | 22-40 [ ] | 95-115 [ ] | 3 [ ] | 3 [ ] |  |
| Nylon PA12 (`pa12`) | printable-polymer | 1010-1040 [ ] | 1.3-2 [ ] | 35-50 [ ] | 90-120 [ ] | 40-90 [ ] | 100-130 [ ] | 4 [ ] | 3 [ ] |  |
| Nylon PA6 (`pa6`) | printable-polymer | 1130-1150 [ ] | 1.5-2.5 [ ] | 40-70 [ ] | 100-120 [ ] | 35-70 [ ] | 110-130 [ ] | 4 [ ] | 3 [ ] |  |
| TPU 95A (flexible) (`tpu`) | printable-polymer | 1100-1230 [ ] | 0.02-0.1 [ ] | 25-45 [ ] | 80-100 [ ] | 25-45 [ ] | 90-110 [ ] | 5 [ ] | 2 [ ] |  |
| Polycarbonate (PC) (`pc`) | printable-polymer | 1190-1210 [ ] | 2-2.5 [ ] | 55-70 [ ] | 110-130 [ ] | 35-60 [ ] | 100-120 [ ] | 5 [ ] | 3 [ ] |  |
| PC-ABS blend (`pc-abs`) | printable-polymer | 1100-1150 [ ] | 1.9-2.4 [ ] | 40-55 [ ] | 95-110 [ ] | 30-55 [ ] | 95-115 [ ] | 4 [ ] | 2 [ ] |  |
| Polypropylene (PP) (`pp`) | printable-polymer | 890-920 [ ] | 0.8-1.4 [ ] | 20-32 [ ] | 90-110 [ ] | 25-45 [ ] | 70-85 [ ] | 4 [ ] | 4 [ ] |  |
| PEEK (`peek`) | printable-polymer | 1290-1320 [ ] | 3.5-4 [ ] | 80-100 [ ] | 240-260 [ ] | 350-800 [ ] | 230-300 [ ] | 3 [ ] | 3 [ ] |  |
| PEI (ULTEM-type) (`pei`) | printable-polymer | 1270-1290 [ ] | 3-3.6 [ ] | 70-90 [ ] | 160-170 [ ] | 150-350 [ ] | 130-170 [ ] | 3 [ ] | 2 [ ] |  |
| PLA-CF (carbon-filled PLA) (`pla-cf`) | printable-composite | 1260-1330 [ ] | 4.5-8 [ ] | 40-65 [ ] | 55-65 [ ] | 30-60 [ ] | 70-100 [ ] | 1 [ ] | 1 [ ] |  |
| PETG-CF (`petg-cf`) | printable-composite | 1300-1380 [ ] | 3.5-6 [ ] | 45-70 [ ] | 70-80 [ ] | 35-65 [ ] | 100-130 [ ] | 2 [ ] | 1 [ ] |  |
| ABS-CF (`abs-cf`) | printable-composite | 1080-1150 [ ] | 3-6 [ ] | 40-60 [ ] | 90-100 [ ] | 35-60 [ ] | 120-150 [ ] | 2 [ ] | 1 [ ] |  |
| PA-CF (carbon-filled nylon) (`pa-cf`) | printable-composite | 1050-1200 [ ] | 4-9 [ ] | 55-100 [ ] | 110-150 [ ] | 70-150 [ ] | 140-180 [ ] | 3 [ ] | 1 [ ] |  |
| PA-GF (glass-filled nylon) (`pa-gf`) | printable-composite | 1180-1330 [ ] | 3-6 [ ] | 50-85 [ ] | 110-150 [ ] | 55-120 [ ] | 110-140 [ ] | 3 [ ] | 1 [ ] |  |
| PC-CF (carbon-filled polycarbonate) (`pc-cf`) | printable-composite | 1230-1300 [ ] | 5-9 [ ] | 60-95 [ ] | 120-140 [ ] | 90-160 [ ] | 140-170 [ ] | 3 [ ] | 1 [ ] |  |
| PEEK-CF (`peek-cf`) | printable-composite | 1380-1440 [ ] | 8-15 [ ] | 100-140 [ ] | 240-260 [ ] | 500-1000 [ ] | 270-350 [ ] | 3 [ ] | 1 [ ] |  |
| Carbon/epoxy (quasi-isotropic laminate) (`cfrp-qi`) | fibre-composite | 1500-1600 [ ] | 45-60 [ ] | 450-700 [ ] | 90-130 [ ] | 80-300 [ ] | 200-380 [ ] | 2 [ ] | 1 [ ] |  |
| Carbon/epoxy (woven 0/90 laminate) (`cfrp-woven`) | fibre-composite | 1450-1600 [ ] | 52-65 [ ] | 500-750 [ ] | 90-130 [ ] | 70-250 [ ] | 200-380 [ ] | 2 [ ] | 1 [ ] |  |
| Glass/epoxy (woven laminate) (`gfrp-woven`) | fibre-composite | 1800-2000 [ ] | 18-28 [ ] | 250-450 [ ] | 90-130 [ ] | 8-25 [ ] | 30-60 [ ] | 3 [ ] | 1 [ ] |  |
| Aramid/epoxy (woven laminate) (`afrp-woven`) | fibre-composite | 1300-1400 [ ] | 25-35 [ ] | 350-550 [ ] | 90-120 [ ] | 60-160 [ ] | 130-230 [ ] | 5 [ ] | 1 [ ] |  |
| Basalt/epoxy (woven laminate) (`bfrp-woven`) | fibre-composite | 1900-2100 [ ] | 20-32 [ ] | 300-500 [ ] | 100-140 [ ] | 10-30 [ ] | 30-70 [ ] | 3 [ ] | 1 [ ] |  |
| Flax/epoxy (woven laminate) (`flax-epoxy`) | fibre-composite | 1250-1400 [ ] | 10-20 [ ] | 80-200 [ ] | 70-100 [ ] | 8-25 [ ] | 55-100 [ ] | 2 [ ] | 1 [ ] |  |
| Hemp-PLA (moulded biocomposite) (`hemp-pla`) | fibre-composite | 1250-1350 [ ] | 4-9 [ ] | 40-90 [ ] | 50-60 [ ] | 10-30 [ ] | 35-60 [ ] | 2 [ ] | 3 [ ] |  |
| Aluminium 6061-T6 (`al6061`) | metal | 2690-2720 [ ] | 68-71 [ ] | 290-320 [ ] | 120-160 [ ] | 4-12 [ ] | 140-220 [ ] | 4 [ ] | 5 [ ] |  |
| Aluminium 7075-T6 (`al7075`) | metal | 2780-2820 [ ] | 70-73 [ ] | 520-580 [ ] | 100-130 [ ] | 6-18 [ ] | 150-230 [ ] | 3 [ ] | 5 [ ] |  |
| Aluminium 5052-H32 (sheet) (`al5052`) | metal | 2660-2690 [ ] | 69-71 [ ] | 210-250 [ ] | 100-150 [ ] | 4-9 [ ] | 140-210 [ ] | 4 [ ] | 5 [ ] |  |
| Titanium Ti-6Al-4V (`ti64`) | metal | 4420-4450 [ ] | 110-118 [ ] | 900-1100 [ ] | 300-400 [ ] | 50-200 [ ] | 550-900 [ ] | 4 [ ] | 4 [ ] |  |
| Magnesium AZ31 (`mg-az31`) | metal | 1770-1790 [ ] | 44-45 [ ] | 240-290 [ ] | 100-150 [ ] | 5-15 [ ] | 250-380 [ ] | 3 [ ] | 4 [ ] |  |
| Stainless steel 304 (`ss304`) | metal | 7900-8000 [ ] | 190-200 [ ] | 500-700 [ ] | 600-870 [ ] | 3-8 [ ] | 60-100 [ ] | 5 [ ] | 5 [ ] |  |
| Balsa wood (`balsa`) | natural-core | 100-200 [ ] | 2-5 [ ] | 8-22 [ ] | 60-80 [ ] | 15-50 [ ] | 4-12 [ ] | 2 [ ] | 4 [ ] |  |
| Birch plywood (aircraft/hobby grade) (`plywood`) | natural-core | 600-720 [ ] | 8-13 [ ] | 30-60 [ ] | 60-80 [ ] | 3-12 [ ] | 8-18 [ ] | 3 [ ] | 3 [ ] |  |
| Bamboo laminate (`bamboo`) | natural-core | 600-750 [ ] | 9-16 [ ] | 60-130 [ ] | 60-80 [ ] | 3-10 [ ] | 4-14 [ ] | 3 [ ] | 4 [ ] |  |
| Agglomerated cork sheet (`cork`) | natural-core | 120-250 [ ] | 0.01-0.05 [ ] | 0.5-2 [ ] | 100-120 [ ] | 5-15 [ ] | 4-16 [ ] | 4 [ ] | 4 [ ] |  |
| EPP foam (`epp`) | natural-core | 20-60 [ ] | 0.004-0.015 [ ] | 0.2-0.8 [ ] | 90-110 [ ] | 4-12 [ ] | 75-100 [ ] | 5 [ ] | 3 [ ] |  |
| EPS foam (`eps`) | natural-core | 12-35 [ ] | 0.003-0.012 [ ] | 0.1-0.4 [ ] | 70-80 [ ] | 2-8 [ ] | 80-100 [ ] | 1 [ ] | 2 [ ] |  |
| XPS foam board (`xps`) | natural-core | 28-45 [ ] | 0.01-0.025 [ ] | 0.2-0.6 [ ] | 70-75 [ ] | 3-8 [ ] | 80-105 [ ] | 1 [ ] | 2 [ ] |  |
| PET structural foam core (`pet-foam`) | natural-core | 60-130 [ ] | 0.04-0.12 [ ] | 1-3 [ ] | 100-130 [ ] | 10-25 [ ] | 70-100 [ ] | 3 [ ] | 3 [ ] |  |
| Aluminium honeycomb core (`al-honeycomb`) | natural-core | 30-100 [ ] | 0.2-1 [ ] | 1.5-5 [ ] | 120-175 [ ] | 40-120 [ ] | 150-230 [ ] | 3 [ ] | 4 [ ] |  |
| Aerogel-core panel (`aerogel-panel`) | natural-core | 100-250 [ ] | 0.005-0.05 [ ] | 0.1-1 [ ] | 150-400 [ ] | 100-400 [ ] | 100-350 [ ] | 2 [ ] | 1 [ ] |  |
| Recycled PET (rPET) (`rpet`) | recycled | 1260-1370 [ ] | 1.8-2.8 [ ] | 35-55 [ ] | 60-75 [ ] | 15-30 [ ] | 25-55 [ ] | 2 [ ] | 4 [ ] |  |
| Recycled nylon (rPA) (`rpa`) | recycled | 1110-1160 [ ] | 1.2-2.4 [ ] | 35-60 [ ] | 90-115 [ ] | 30-70 [ ] | 35-75 [ ] | 3 [ ] | 4 [ ] |  |
| Recycled polypropylene (rPP) (`rpp`) | recycled | 900-940 [ ] | 0.8-1.4 [ ] | 18-30 [ ] | 85-100 [ ] | 15-35 [ ] | 15-40 [ ] | 3 [ ] | 4 [ ] |  |
| Recycled PLA (rPLA) (`rpla`) | recycled | 1240-1280 [ ] | 2.2-3.4 [ ] | 35-55 [ ] | 50-58 [ ] | 18-32 [ ] | 25-45 [ ] | 1 [ ] | 3 [ ] |  |

## Property basis per record

| Material | Basis stated in the data |
|---|---|
| PLA | Printed specimens, XY (in-plane) orientation, typical FDM settings; cost is filament/stock price per kg. |
| PLA+ (toughened PLA) | Printed specimens, XY (in-plane) orientation, typical FDM settings; cost is filament/stock price per kg. |
| PETG | Printed specimens, XY (in-plane) orientation, typical FDM settings; cost is filament/stock price per kg. |
| ABS | Printed specimens, XY (in-plane) orientation, typical FDM settings; cost is filament/stock price per kg. |
| ASA | Printed specimens, XY (in-plane) orientation, typical FDM settings; cost is filament/stock price per kg. |
| Nylon PA12 | Printed specimens, XY (in-plane) orientation, typical FDM settings; cost is filament/stock price per kg. |
| Nylon PA6 | Printed specimens, XY (in-plane) orientation, typical FDM settings; cost is filament/stock price per kg. |
| TPU 95A (flexible) | Printed specimens, XY (in-plane) orientation, typical FDM settings; cost is filament/stock price per kg. |
| Polycarbonate (PC) | Printed specimens, XY (in-plane) orientation, typical FDM settings; cost is filament/stock price per kg. |
| PC-ABS blend | Printed specimens, XY (in-plane) orientation, typical FDM settings; cost is filament/stock price per kg. |
| Polypropylene (PP) | Printed specimens, XY (in-plane) orientation, typical FDM settings; cost is filament/stock price per kg. |
| PEEK | Printed specimens, XY (in-plane) orientation, typical FDM settings; cost is filament/stock price per kg. |
| PEI (ULTEM-type) | Printed specimens, XY (in-plane) orientation, typical FDM settings; cost is filament/stock price per kg. |
| PLA-CF (carbon-filled PLA) | Short-fibre-filled filament printed in XY (in-plane) orientation; fibre fraction typical of commercial filaments; cost is filament price per kg. |
| PETG-CF | Short-fibre-filled filament printed in XY (in-plane) orientation; fibre fraction typical of commercial filaments; cost is filament price per kg. |
| ABS-CF | Short-fibre-filled filament printed in XY (in-plane) orientation; fibre fraction typical of commercial filaments; cost is filament price per kg. |
| PA-CF (carbon-filled nylon) | Short-fibre-filled filament printed in XY (in-plane) orientation; fibre fraction typical of commercial filaments; cost is filament price per kg. |
| PA-GF (glass-filled nylon) | Short-fibre-filled filament printed in XY (in-plane) orientation; fibre fraction typical of commercial filaments; cost is filament price per kg. |
| PC-CF (carbon-filled polycarbonate) | Short-fibre-filled filament printed in XY (in-plane) orientation; fibre fraction typical of commercial filaments; cost is filament price per kg. |
| PEEK-CF | Short-fibre-filled filament printed in XY (in-plane) orientation; fibre fraction typical of commercial filaments; cost is filament price per kg. |
| Carbon/epoxy (quasi-isotropic laminate) | Laminate at roughly 50% fibre volume, in-plane properties of a quasi-isotropic or balanced woven layup (not unidirectional); cost is raw laminate material per kg. |
| Carbon/epoxy (woven 0/90 laminate) | Laminate at roughly 50% fibre volume, in-plane properties of a quasi-isotropic or balanced woven layup (not unidirectional); cost is raw laminate material per kg. |
| Glass/epoxy (woven laminate) | Laminate at roughly 50% fibre volume, in-plane properties of a quasi-isotropic or balanced woven layup (not unidirectional); cost is raw laminate material per kg. |
| Aramid/epoxy (woven laminate) | Laminate at roughly 50% fibre volume, in-plane properties of a quasi-isotropic or balanced woven layup (not unidirectional); cost is raw laminate material per kg. |
| Basalt/epoxy (woven laminate) | Laminate at roughly 50% fibre volume, in-plane properties of a quasi-isotropic or balanced woven layup (not unidirectional); cost is raw laminate material per kg. |
| Flax/epoxy (woven laminate) | Laminate at roughly 50% fibre volume, in-plane properties of a quasi-isotropic or balanced woven layup (not unidirectional); cost is raw laminate material per kg. |
| Hemp-PLA (moulded biocomposite) | Compression-moulded or injection-moulded sheet with roughly 30% hemp fibre, in-plane values (random mat); not a printed filament. |
| Aluminium 6061-T6 | Wrought material, isotropic, in the temper named; cost is stock price per kg. |
| Aluminium 7075-T6 | Wrought material, isotropic, in the temper named; cost is stock price per kg. |
| Aluminium 5052-H32 (sheet) | Wrought material, isotropic, in the temper named; cost is stock price per kg. |
| Titanium Ti-6Al-4V | Wrought material, isotropic, in the temper named; cost is stock price per kg. |
| Magnesium AZ31 | Wrought material, isotropic, in the temper named; cost is stock price per kg. |
| Stainless steel 304 | Wrought material, isotropic, in the temper named; cost is stock price per kg. |
| Balsa wood | Along-grain values for grades from about 100 to 200 kg/m3; strong grain-direction dependence. |
| Birch plywood (aircraft/hobby grade) | Typical values along the stronger in-plane/grain direction for the density grade stated; foams use compressive modulus as the stiffness figure. |
| Bamboo laminate | Typical values along the stronger in-plane/grain direction for the density grade stated; foams use compressive modulus as the stiffness figure. |
| Agglomerated cork sheet | Typical values along the stronger in-plane/grain direction for the density grade stated; foams use compressive modulus as the stiffness figure. |
| EPP foam | Bulk foam; compressive modulus used as stiffness; strength is the typical tensile or compressive figure. |
| EPS foam | Bulk foam; compressive modulus used as stiffness; strength is the typical tensile or compressive figure. |
| XPS foam board | Bulk foam; compressive modulus used as stiffness; strength is the typical tensile or compressive figure. |
| PET structural foam core | Bulk core foam; compressive modulus used as stiffness; only meaningful as a sandwich core. |
| Aluminium honeycomb core | Effective out-of-plane (through-thickness) compressive properties of the core; only meaningful as a sandwich core. |
| Aerogel-core panel | Effective panel properties for an aerogel-blanket-cored sandwich; wide ranges reflect high uncertainty. |
| Recycled PET (rPET) | Printed specimens, XY (in-plane) orientation, recycled-content filament; cost is filament price per kg. |
| Recycled nylon (rPA) | Printed specimens, XY (in-plane) orientation, recycled-content filament; cost is filament price per kg. |
| Recycled polypropylene (rPP) | Printed specimens, XY (in-plane) orientation, recycled-content filament; cost is filament price per kg. |
| Recycled PLA (rPLA) | Printed specimens, XY (in-plane) orientation, recycled-content filament; cost is filament price per kg. |
