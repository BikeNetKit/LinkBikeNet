"""Overpass settings for `linkbikenet`. Do not change."""

_op_ref = "LinkBikeNet Python package (https://github.com/BikeNetKit/LinkBikeNet)"

import osmnx.settings as oxs
oxs.http_user_agent = _op_ref
oxs.http_referer = _op_ref