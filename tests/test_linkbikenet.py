import geopandas as gpd
import pytest
from pandas.testing import assert_frame_equal
import linkbikenet as lbn

lbn.constants.TOP_CLOSEST_COMPONENTS = 5

@pytest.fixture
def validation_gdf_frederiksberg_cc():
    gdf = gpd.read_file("./tests/test_data/frederiksberg-linkbikenet-closest_components.gpkg", layer='Identified links')
    return gdf[['network_length', 'lcc_length', 'link_length', 'num_components_added', 'lcc_share', 'lcc_gain', 'ordering']]

def test_linkbikenet_closest_components_case_success_offline1(validation_gdf_frederiksberg_cc):
    """Verify that the offline version of fixbikenet, closest_components works 
    as intended.
    """
    linked_components = lbn.linkbikenet(
        "Frederiksberg", 
        connection_strategy='closest_components',
        import_files={
            'city_boundary': "./tests/test_data/frederiksberg_boundary.geojson",
            'street_network': "./tests/test_data/frederiksberg_streetbike_network.gpkg",
        },
    )
    assert_frame_equal(
        validation_gdf_frederiksberg_cc,
        linked_components[['network_length', 'lcc_length', 'link_length', 'num_components_added', 'lcc_share', 'lcc_gain', 'ordering']]
    )


@pytest.fixture
def validation_gdf_frederiksberg_l2c():
    gdf = gpd.read_file("./tests/test_data/frederiksberg-linkbikenet-largest_to_closest.gpkg", layer='Identified links')
    return gdf[['network_length', 'lcc_length', 'link_length', 'num_components_added', 'lcc_share', 'lcc_gain', 'ordering']]

def test_linkbikenet_largest_to_closest_case_success_offline1(validation_gdf_frederiksberg_l2c):
    """Verify that the offline version of fixbikenet, closest_components works 
    as intended.
    """
    linked_components = lbn.linkbikenet(
        "Frederiksberg", 
        connection_strategy='largest_to_closest',
        import_files={
            'city_boundary': "./tests/test_data/frederiksberg_boundary.geojson",
            'street_network': "./tests/test_data/frederiksberg_streetbike_network.gpkg",
        },
    )
    assert_frame_equal(
        validation_gdf_frederiksberg_l2c,
        linked_components[['network_length', 'lcc_length', 'link_length', 'num_components_added', 'lcc_share', 'lcc_gain', 'ordering']]
    )


@pytest.fixture
def validation_gdf_frederiksberg_l2s():
    gdf = gpd.read_file("./tests/test_data/frederiksberg-linkbikenet-largest_to_second.gpkg", layer='Identified links')
    return gdf[['network_length', 'lcc_length', 'link_length', 'num_components_added', 'lcc_share', 'lcc_gain', 'ordering']]

def test_linkbikenet_largest_to_second_case_success_offline1(validation_gdf_frederiksberg_l2s):
    """Verify that the offline version of fixbikenet, closest_components works 
    as intended.
    """
    linked_components = lbn.linkbikenet(
        "Frederiksberg", 
        connection_strategy='largest_to_second',
        import_files={
            'city_boundary': "./tests/test_data/frederiksberg_boundary.geojson",
            'street_network': "./tests/test_data/frederiksberg_streetbike_network.gpkg",
        },
    )
    assert_frame_equal(
        validation_gdf_frederiksberg_l2s,
        linked_components[['network_length', 'lcc_length', 'link_length', 'num_components_added', 'lcc_share', 'lcc_gain', 'ordering']]
    )