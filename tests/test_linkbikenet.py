import geopandas as gpd
import pytest
from pandas.testing import assert_frame_equal
import linkbikenet as lbn

import_path = './tests/test_data/'
lbn.settings.import_path = import_path
valcols = ['network_length', 'lcc_length', 'link_length', 'num_components_added', 'lcc_share', 'lcc_gain', 'ordering']


# Online tests

def test_linkbikenet_success_online_mwe():
    """Verify that the online version of linkbikenet does not throw an error, 
    minimal working example.
    """
    linked_components = lbn.linkbikenet(
        city_query="Oelde",
    )

def test_linkbikenet_success_online_mwe_city_boundary():
    """Verify that the online version of linkbikenet does not throw an error, 
    minimal working example with imported city boundary.
    """
    linked_components = lbn.linkbikenet(
        city_query="Oelde",
        import_files={
            'city_boundary': "oelde_boundary.geojson",
        },
    )


# Offline tests

@pytest.fixture
def validation_gdf_frederiksberg_cc():
    gdf = gpd.read_file(lbn.settings.import_path+"frederiksberg-linkbikenet-closest_components.gpkg", layer='Identified links')
    return gdf

def test_linkbikenet_closest_components_success_offline1(validation_gdf_frederiksberg_cc):
    """Verify that the offline version of fixbikenet, closest_components works 
    as intended.
    """
    lbn.constants.TOP_CLOSEST_COMPONENTS = 5
    linked_components = lbn.linkbikenet(
        "Frederiksberg", 
        link_strategy='closest_components',
        import_files={
            'city_boundary': "frederiksberg_boundary.geojson",
            'street_network': "frederiksberg_streetbike_network.gpkg",
        },
    )
    assert_frame_equal(
        validation_gdf_frederiksberg_cc[valcols],
        linked_components[valcols]
    )


@pytest.fixture
def validation_gdf_frederiksberg_l2c():
    gdf = gpd.read_file(lbn.settings.import_path+"frederiksberg-linkbikenet-largest_to_closest.gpkg", layer='Identified links')
    return gdf

def test_linkbikenet_largest_to_closest_success_offline1(validation_gdf_frederiksberg_l2c):
    """Verify that the offline version of fixbikenet, closest_components works 
    as intended.
    """
    lbn.constants.TOP_CLOSEST_COMPONENTS = 5
    linked_components = lbn.linkbikenet(
        "Frederiksberg", 
        link_strategy='largest_to_closest',
        import_files={
            'city_boundary': "frederiksberg_boundary.geojson",
            'street_network': "frederiksberg_streetbike_network.gpkg",
        },
    )
    assert_frame_equal(
        validation_gdf_frederiksberg_l2c[valcols],
        linked_components[valcols]
    )


@pytest.fixture
def validation_gdf_frederiksberg_l2s():
    gdf = gpd.read_file(lbn.settings.import_path+"frederiksberg-linkbikenet-largest_to_second.gpkg", layer='Identified links')
    return gdf

def test_linkbikenet_largest_to_second_success_offline1(validation_gdf_frederiksberg_l2s):
    """Verify that the offline version of fixbikenet, closest_components works 
    as intended.
    """
    lbn.constants.TOP_CLOSEST_COMPONENTS = 5
    linked_components = lbn.linkbikenet(
        "Frederiksberg", 
        link_strategy='largest_to_second',
        import_files={
            'city_boundary': "frederiksberg_boundary.geojson",
            'street_network': "frederiksberg_streetbike_network.gpkg",
        },
    )
    assert_frame_equal(
        validation_gdf_frederiksberg_l2s[valcols],
        linked_components[valcols]
    )