"""Global settings for `linkbikenet` that can be configured by the user.

export_path : dict(str)
    Paths to results and plots folders to save data and plots.
import_path : str
    Path to import files (as defined in `growbikenet`'s import_files parameter).
silent : bool, default False
    If set to True, suppresses all user feedback. Useful for batch exports.
"""

crs_projected = 'auto'
export_path = {
    "results":"./results/",
}
import_path = "./"
silent = False