import networkx as nx
import pytest
from linkbikenet.utils import (
    _validate_parameters,
    _validate_settings,
    pair_between_largest_components,
    pair_between_largest_and_closest_components,
    pair_between_closest_components
)
from linkbikenet import constants, settings

constants.TOP_CLOSEST_COMPONENTS = 1

def test_validate_parameters():
    with pytest.raises(TypeError):
        _validate_parameters(city_query=7, link_strategy='largest_to_second', export_data=False, city_id=None, import_files={})
    with pytest.raises(TypeError):
        _validate_parameters(city_query='Budapest', link_strategy='test', export_data=False, city_id=None,
                             import_files={})
    with pytest.raises(TypeError):
        _validate_parameters(city_query='Budapest', link_strategy='largest_to_second', export_data=7, city_id=None,
                             import_files={})
    with pytest.raises(TypeError):
        _validate_parameters(city_query='Budapest', link_strategy='largest_to_second', export_data=False, city_id=7,
                             import_files={})
    with pytest.raises(TypeError):
        _validate_parameters(city_query='Budapest', link_strategy='largest_to_second', export_data=False, city_id=None,
                             import_files=7)

def test_validate_settings():
    constants._CRS_CALCULATIONS = 7
    with pytest.raises(TypeError):
        _validate_settings()
    constants._CRS_CALCULATIONS = 'auto'
    settings.export_file_format = 'test'
    with pytest.raises(ValueError):
        _validate_settings()
    settings.export_file_format = 'gpkg'

@pytest.fixture
def create_test_components_largest():
    G = nx.Graph()
    G.add_nodes_from([(1, {"x": 1, "y": 2}), (2, {"x": 5, "y": 6}), (3, {"x": 7, "y": 8}), (4, {"x": 10, "y": 10}), (5, {"x": 11, "y": 11}), (6, {"x": 15, "y": 20})])
    G.add_edges_from([(1, 2, {'length': 5}), (2, 3, {'length': 2}), (1, 3, {'length': 7}), (4, 5, {'length': 1})])
    wcc = [G.subgraph(c).copy() for c in sorted(nx.connected_components(G), key=lambda c: sum(
        [l[-1] for l in G.subgraph(c).copy().edges.data('length')]), reverse=True)]
    return wcc

@pytest.fixture
def create_test_graph_largest():
    G = nx.Graph()
    G.add_nodes_from([(1, {"x": 1, "y": 2}), (2, {"x": 5, "y": 6}), (3, {"x": 7, "y": 8}), (4, {"x": 10, "y": 10}), (5, {"x": 11, "y": 11}), (6, {"x": 15, "y": 20})])
    G.add_edges_from([(1, 2, {'length': 5}), (2, 3, {'length': 2}), (1, 3, {'length': 7}), (4, 5, {'length': 1})])
    G.add_edges_from([(3, 4, {'length': 1})])
    return G

@pytest.fixture
def create_validation_pair_largest():
    pair = 3,4
    return pair

def test_pair_between_largest_components(create_test_components_largest, create_test_graph_largest, create_validation_pair_largest):
    res = pair_between_largest_components(create_test_graph_largest, create_test_components_largest).iloc[0]
    assert (res.lcc_nodeid, res.comp_nodeid) == create_validation_pair_largest


@pytest.fixture
def create_test_components_nearest():
    G = nx.Graph()
    G.add_nodes_from([(1, {"x": 1, "y": 2}), (2, {"x": 5, "y": 6}), (3, {"x": 7, "y": 8}), (4, {"x": 30, "y": 30}), (5, {"x": 31, "y": 31}), (6, {"x": 10, "y": 10})])
    G.add_edges_from([(1, 2, {'length': 5}), (2, 3, {'length': 2}), (1, 3, {'length': 7}), (4, 5, {'length': 1})])
    wcc = [G.subgraph(c).copy() for c in sorted(nx.connected_components(G), key=lambda c: sum(
        [l[-1] for l in G.subgraph(c).copy().edges.data('length')]), reverse=True)]
    return wcc

@pytest.fixture
def create_validation_pair_nearest():
    pair = 3,6
    return pair

def test_pair_between_nearest_components(create_test_components_nearest, create_validation_pair_nearest):
    res = pair_between_largest_and_closest_components(create_test_components_nearest).iloc[0]
    assert (res.lcc_nodeid, res.comp_nodeid) == create_validation_pair_nearest

@pytest.fixture
def create_test_components_closest():
    G = nx.Graph()
    G.add_nodes_from([(1, {"x": 1, "y": 1}), (2, {"x": 2, "y": 2}), (3, {"x": 1, "y": 2}), (4, {"x": 30, "y": 30}), (5, {"x": 31, "y": 31}), (6, {"x": 10, "y": 10})])
    G.add_edges_from([(1, 2, {'length': 5}), (2, 3, {'length': 2}), (1, 3, {'length': 7}), (4, 5, {'length': 1})])
    wcc = [G.subgraph(c).copy() for c in sorted(nx.connected_components(G), key=lambda c: sum(
        [l[-1] for l in G.subgraph(c).copy().edges.data('length')]), reverse=True)]
    return wcc

@pytest.fixture
def create_validation_pair_closest():
    pair = 2,6
    return pair

def test_pair_between_closest_components(create_test_components_closest, create_validation_pair_closest):
    res = pair_between_closest_components(create_test_components_closest).iloc[0]
    assert (res.lcc_nodeid, res.comp_nodeid) == create_validation_pair_closest
