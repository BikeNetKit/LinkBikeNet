"""Global constants for `linkbikenet` that can be tweaked during development, but 
should not be changed later by the user. Especially technical or internal 
constants start with an underscore.

_PROGRESS_BAR_DESC_LENGTH : int, default 21
    Character length of tqdm progress bar descriptions. This is the space given 
    to text like "Importing network data ", which is at the maximum of 23 
    characters.
_PROGRESS_BAR_LENGTH : int, default 23
    Character length of tqdm progress bars.
"""

_PROGRESS_BAR_DESC_LENGTH = 21
_PROGRESS_BAR_LENGTH = 23
