"""Example of linkbikenet used during package development."""

import linkbikenet as lbn

lbn.settings.import_path = '/Users/mszell/Tresorit/bikenetkitshare/'
city_id = "frederiksberg_dk"

lbn.settings.import_path = './tests/test_data/'
lbn.constants.TOP_CLOSEST_COMPONENTS = 5
lbn.settings.export_file_format = "gpkg"

linked_components = lbn.linkbikenet(
	"Frederiksberg", 
	link_strategy='closest_components',
	import_files={
		'city_boundary': "frederiksberg_boundary.geojson",
        'street_network': "frederiksberg_streetbike_network.gpkg",
    },
    export_data = True,
)

# print(edges_ordered['network_length'])