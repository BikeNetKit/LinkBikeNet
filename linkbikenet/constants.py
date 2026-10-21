"""Global constants for `linkbikenet` that can be tweaked during development, 
but should not be changed later by the user. Especially technical or internal 
constants start with an underscore.

TOP_CLOSEST_COMPONENTS : int, default 5
    The number of top closest components to try to route to, for finding the
    one with shortest path distance. The higher, the more accurate, but also 
    more computations.
_CRS_CALCULATIONS : str, default 'auto'
    EPSG code of the coordinate reference system that is used to project OSM 
    data for calculations. This has to be a distance-preserving projected CRS, 
    so '3857' (WGS 84 / Pseudo-Mercator) would be wrong! Option 'auto' selects
    the best UTM via `estimate_utm_crs()`.
_PROGRESS_BAR_DESC_LENGTH : int, default 21
    Character length of tqdm progress bar descriptions. This is the space given 
    to text like "Importing network data ", which is at the maximum of 23 
    characters.
_PROGRESS_BAR_LENGTH : int, default 23
    Character length of tqdm progress bars.
"""

TOP_CLOSEST_COMPONENTS = 5
_CRS_CALCULATIONS = 'auto'
_PROGRESS_BAR_DESC_LENGTH = 23
_PROGRESS_BAR_LENGTH = 23
