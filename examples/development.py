"""Example of linkbikenet used during package development."""

import linkbikenet as lbn

edges_ordered = lbn.linkbikenet(
	"Riga", 
	connection_strategy='largest_to_closest'
)