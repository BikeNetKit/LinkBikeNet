"""Example of linkbikenet used during package development."""

import linkbikenet as lbn

lbn.settings.import_path = '/Users/mszell/Tresorit/bikenetkitshare/'
city_id = "frederiksberg_dk"
lbn.constants.TOP_CLOSEST_COMPONENTS = 5
lbn.settings.export_file_format = "geojson"

edges_ordered = lbn.linkbikenet(
	"Frederiksberg", 
	link_strategy='largest_to_second',
	import_files={
		'city_boundary': 'boundaries/'+city_id+'.geojson',
        'street_network': 'streetbike_networks/'+city_id+'.gpkg',
    },
)

# print(edges_ordered['network_length'])