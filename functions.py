import config
import geopandas as gpd
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import LineString

def map_edges_to_bike_infrastructure(g):
    """
    map if edges in graph have bike infrastructure as specified in config.py

    Parameters
    ----------
    g :networkx.MultiDiGraph
        simplified graph representing the street network

    Returns
    -------
    g : networkx.MultiDiGraph
        simplified graph representing the street network, with added binary edge attribute "pbi"
    """

    # add binary edge attribute "pbi" (protected bike infra: True/False)
    for edge in g.edges(keys=True):
        if g.edges[edge].get("cycleway") in config.cycleway_bike_infra:
            g.edges[edge]["pbi"] = 1
        elif g.edges[edge].get("cycleway:right") in config.cycleway_right_bike_infra:
            g.edges[edge]["pbi"] = 1
        elif g.edges[edge].get("cycleway:left") in config.cycleway_left_bike_infra:
            g.edges[edge]["pbi"] = 1
        elif g.edges[edge].get("cycleway:both") in config.cycleway_both_bike_infra:
            g.edges[edge]["pbi"] = 1
        elif g.edges[edge].get("highway") in config.highway_bike_infra:
            g.edges[edge]["pbi"] = 1
        else:
            g.edges[edge]["pbi"] = 0
    return g

def find_edges_to_drop(g):
    """
    find parallel edges that have different pbi values, list the ones with pbi=0

    Parameters
    ----------
    g : networkx.MultiDiGraph
        simplified graph representing the street network, with added binary edge attribute "pbi"

    Returns
    -------
    edges_to_drop: list
        unique list of edges to drop-> edges where pbi values differ and pbi value=0 gets dropped
    """
    # to find parallel edges, get all u,v tuples for which u,v,w>0 exists:
    uvs = [edge[:2] for edge in list(g.edges) if edge[2] > 0]  # >0 includes key=1, key=2, ...
    uvs = list(set(uvs))
    edges_to_drop = []

    for uv in uvs:
        # collect all parallel edges for u-v node pair;
        # account for the fact that edges are directed! uv[::-1]==vu might also be on the list
        parallel_edges = [edge for edge in list(g.edges) if (edge[:2] == uv) or (edge[:2] == uv[::-1])]

        # get set of PBIs for this u-v parallel edge list
        pbis = set([g.edges[e]["pbi"] for e in parallel_edges])

        # if we have both pbi==0 and pbi==1,
        if len(pbis) == 2:
            # add edges with pbi==0 to edges_to_drop list
            to_drop = [e for e in parallel_edges if g.edges[e]["pbi"] == 0]
            edges_to_drop += to_drop

    edges_to_drop = list(set(edges_to_drop))
    return edges_to_drop

def graph_edges_to_gdf(G):
    """
    Parameters
    ----------
    G: networkx.Graph
        undirected simple graph representing the street network with weighted edges

    Returns
    -------
    edges_gdf: geopandas.GeoDataFrame
        geodataframe with edges from G, including edge attributes
    """
    rows = []
    for u, v, data in G.edges(data=True):
        # if geometry already exists on the edge, use it
        if "geometry" in data:
            geom = data["geometry"]
        else:
            # otherwise build a straight line from node coordinates
            geom = LineString([
                (G.nodes[u]["x"], G.nodes[u]["y"]),
                (G.nodes[v]["x"], G.nodes[v]["y"])
            ])
        rows.append({
            "u": u,
            "v": v,
            **data,
            "geometry": geom
        })
    edges_gdf = gpd.GeoDataFrame(
        rows,
        geometry="geometry",
        crs=G.graph.get("crs")
    ).set_index(["u", "v"])

    return edges_gdf

def pair_between_largest_components(wcc):
    """
    Find the closest pair of nodes between the two largest components
    using a KD-tree.
    Parameters
    ----------
    components : list of networkx.Graph
        Components sorted with the largest first.
    Returns
    -------
    closest_pair : tuple
        The two nodes that should be connected
    """
    G1 = wcc[0]
    G2 = wcc[1]

    # Coordinates of nodes in the second component
    nodes2 = list(G2.nodes())
    coords2 = np.array([
        (G2.nodes[n]["x"], G2.nodes[n]["y"])
        for n in nodes2
    ])
    # Build KD-tree
    tree = cKDTree(coords2)
    closest_pair = None
    min_dist = np.inf

    # Query the nearest node in G2 for every node in G1
    for n1, data in G1.nodes(data=True):
        coord = np.array([data["x"], data["y"]])
        dist, idx = tree.query(coord)
        if dist < min_dist:
            min_dist = dist
            closest_pair = (n1, nodes2[idx])

    return closest_pair

def pair_between_nearest_components(wcc):
    """
    Find the pair of nodes connecting the largest component to the
    geographically nearest remaining component.

    Parameters
    ----------
    wcc : list of nx.Graph
        Connected components sorted with the largest first.

    Returns
    -------
    closest_pair : tuple
        The two nodes that should be connected
    """

    largest = wcc[0]

    # Build KD-tree for the largest component
    largest_nodes = list(largest.nodes())
    largest_xy = np.array([
        (largest.nodes[n]["x"], largest.nodes[n]["y"])
        for n in largest_nodes
    ])
    tree = cKDTree(largest_xy)

    closest_pair = None
    best_distance = np.inf
    # Compare every remaining component to the largest
    for comp in wcc[1:]:
        comp_nodes = list(comp.nodes())
        comp_xy = np.array([
            (comp.nodes[n]["x"], comp.nodes[n]["y"])
            for n in comp_nodes
        ])
        distances, indices = tree.query(comp_xy)
        i = np.argmin(distances)
        if distances[i] < best_distance:
            best_distance = distances[i]
            closest_pair = (
                largest_nodes[indices[i]],
                comp_nodes[i]
            )
    return closest_pair

def get_correct_edgetuples(edge_gdf, nodelist):
    """
    helper function that maps a node list (output of nx.shortest_paths)
    to the correct set of edge tuples that can be used for INDEXING THE EDGE GDF

    Parameters
    ----------
    edge_gdf: geopandas.geodataframe.GeoDataFrame
        The street network, in a projected coordinate reference system
    nodelist: list
        A list of nodes that make up source and targets of edges

    Returns
    -------
    edgelist_final: list
        List of edge tuples that can be used for INDEXING THE EDGE GDF
    """
    edgelist_prelim = zip(nodelist, nodelist[1:])
    edgelist_final = []
    temp_gdf = edge_gdf.sort_index() # To circumvent PerformanceWarning, see https://stackoverflow.com/questions/54307300/what-causes-indexing-past-lexsort-depth-warning-in-pandas
    for edge_prelim in edgelist_prelim:
        if edge_prelim in temp_gdf.index:
            edgelist_final.append(edge_prelim)
        else:
            edgelist_final.append(tuple([edge_prelim[1], edge_prelim[0]]))
    return edgelist_final

def create_gdf_with_geoms(df, edges):
    """
    Parameters
    ----------
    df: pandas.DataFrame
        Dataframe with path nodes and path edges
    edges: geopandas.GeoDataFrame
        The street network, in a projected coordinate reference system

    Returns
    -------
    gdf: geopandas.GeoDataFrame
        projected GeoDataFrame with path nodes and path edges and merged geometries
    """
    # get geometry by merging all geoms from edge gdf
    df = df.copy()
    df["geometry"] = df.edge_list.apply(
        lambda x: edges.loc[x].geometry.union_all()
    )
    # convert edges into a gdf
    gdf = gpd.GeoDataFrame(df, crs=edges.crs, geometry="geometry")
    # merge multilinestring into linestring where possible (should be possible everywhere)
    gdf["geometry"] = gdf.line_merge()
    return gdf