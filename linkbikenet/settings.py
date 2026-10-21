"""Global settings for `linkbikenet` that can be configured by the user.

crs_result : str, default '4326'
    EPSG code of the coordinate reference system for the resulting geodataframe
    and exported data. If '4326' (WGS84) and `export_file_format` is set to 
    'geojson', data is exported via the RFC7946 standard.
export_file_format : {'gpkg', 'geojson'}, default 'gpkg'
    File format for the data export, relevant if `export_data` is set to True. 
    If exporting as geojson, generates extra files for seed points, city 
    boundary, and existing bicycle network (if relevant). If exporting as gkpg, 
    these are added all in one file as extra layers.
export_path : dict(str)
    Paths to results and plots folders to save data and plots.
import_path : str
    Path to import files (as defined in `growbikenet`'s import_files parameter).
silent : bool, default False
    If set to True, suppresses all user feedback. Useful for batch exports.
"""

crs_result = '4326'
export_file_format = 'gpkg'
export_path = {
    "results":"./results/",
}
import_path = "./"
silent = False