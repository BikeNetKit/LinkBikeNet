"""Example of linkbikenet used during package development."""

import linkbikenet as lbn

edges_ordered = lbn.linkbikenet(
	"Budapest", 
	connection_strategy='closest_components'
)