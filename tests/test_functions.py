import networkx as nx
import pytest
from linkbikenet.functions import *

@pytest.fixture
def create_test_components_largest():
    G = nx.Graph()
    G.add_nodes_from([(1, {"x": 1, "y": 2}), (2, {"x": 5, "y": 6}), (3, {"x": 7, "y": 8}), (4, {"x": 10, "y": 10}), (5, {"x": 11, "y": 11}), (6, {"x": 15, "y": 20})])
    G.add_edges_from([(1, 2, {'length': 5}), (2, 3, {'length': 2}), (1, 3, {'length': 7}), (4, 5, {'length': 1})])
    wcc = [G.subgraph(c).copy() for c in sorted(nx.connected_components(G), key=lambda c: sum(
        [l[-1] for l in G.subgraph(c).copy().edges.data('length')]), reverse=True)]
    return wcc

@pytest.fixture
def create_validation_pair_largest():
    pair = 3,4
    return pair

def test_pair_between_largest_components(create_test_components_largest, create_validation_pair_largest):
    assert pair_between_largest_components(create_test_components_largest) == create_validation_pair_largest


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
    assert pair_between_largest_and_closest_components(create_test_components_nearest) == create_validation_pair_nearest

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
    assert pair_between_closest_components(create_test_components_closest) == create_validation_pair_closest
