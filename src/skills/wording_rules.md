# Wording rules and templates

Generate sentences from the numbers in the report dict. A language model may polish phrasing but must not change values, direction, or significance.

## Templates

**Significant change**
"At this location, {variable} has {increased|decreased} by about {rate} {unit} per decade over {n_years} years (statistically significant after correcting for testing many locations)."

**Not significant**
"No statistically significant change in {variable} was detected over {n_years} years."

**Low confidence add-on**
"The record is short ({n_years} years), so treat this result with caution."

**Nearby comparison**
- Mostly same direction: "Nearby, {same_pct} of surrounding cells show a significant change in the same direction."
- Mixed: "Nearby, {up_pct} of cells increase and {down_pct} decrease significantly, so this variable is moving in opposite directions within the region."
- Mostly not significant: "Most surrounding cells show no significant change."

## Do and avoid

| Do | Avoid |
|---|---|
| "decreased by 0.8 percent per decade" | "will keep falling" |
| "not statistically significant" | "no change" |
| "associated with" | "caused by", "because of" |
| State the period and years of data | Hide the record length |
| "model-based (reanalysis)" for MERRA-2/GLDAS | Presenting models as observations |
| "coarse resolution, regional average" for GRACE | Implying street-level precision |

## Politically or socially sensitive places
Describe observations neutrally. Do not attribute responsibility to countries, projects, or groups.

## Units
Use the unit stored with the layer. For rates write the unit then "per decade" (for example "mm/month per decade"). Round to 2 significant figures.
