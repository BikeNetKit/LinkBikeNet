"""Example of linkbikenet used during package development."""

import linkbikenet as lbn

lbn.settings.import_path = '/Users/mszell/Tresorit/bikenetkitshare/'
city_id = "oslo_no"

edges_ordered = lbn.linkbikenet(
	"Oslo", 
	connection_strategy='closest_components',
	import_files={
		'city_boundary': 'boundaries/'+city_id+'.geojson',
        'street_network': 'streetbike_networks/'+city_id+'.gpkg',
    },
)