"""Global settings for `linkbikenet` that can be configured by the user.

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

crs_projected = 'auto'
export_file_format = 'gpkg'
export_path = {
    "results":"./results/",
}
import_path = "./"
silent = False