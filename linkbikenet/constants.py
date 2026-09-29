"""Global constants for `linkbikenet` that can be tweaked during development, but 
should not be changed later by the user. Especially technical or internal 
constants start with an underscore.

TOP_CLOSEST_COMPONENTS : int, default 5
    The number of top closest components to try to route to, for finding the
    one with shortest path distance. The higher, the more accurate, but also 
    more computations.
_PROGRESS_BAR_DESC_LENGTH : int, default 21
    Character length of tqdm progress bar descriptions. This is the space given 
    to text like "Importing network data ", which is at the maximum of 23 
    characters.
_PROGRESS_BAR_LENGTH : int, default 23
    Character length of tqdm progress bars.
"""

TOP_CLOSEST_COMPONENTS = 5
_PROGRESS_BAR_DESC_LENGTH = 21
_PROGRESS_BAR_LENGTH = 23
