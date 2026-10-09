"""Example of linkbikenet used during package development."""

import linkbikenet as lbn

lbn.settings.import_path = '/Users/mszell/Tresorit/bikenetkitshare/'
city_id = "frederiksberg_dk"
lbn.constants.TOP_CLOSEST_COMPONENTS = 5

edges_ordered = lbn.linkbikenet(
	"Frederiksberg", 
	connection_strategy='closest_components',
	import_files={
		'city_boundary': 'boundaries/'+city_id+'.geojson',
        'street_network': 'streetbike_networks/'+city_id+'.gpkg',
    },
    export_file_format = "gpkg",
)

print(edges_ordered['network_length'])