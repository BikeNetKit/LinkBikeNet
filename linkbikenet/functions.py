from . import config
from . import settings
from . import constants
import re
import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import LineString
from tqdm import tqdm
import datetime
pd.set_option('display.max_columns', None) # for debugging
import sys  # noqa: F401, use sys.exit() for debugging

def _print_header(city_query, connection_strategy):
    """Print header.
    """
    if not settings.silent:
        print((constants._PROGRESS_BAR_DESC_LENGTH+constants._PROGRESS_BAR_LENGTH)*"=")
        print("RUNNING LINKBIKENET FOR CITY: " + city_query)
        print(connection_strategy)
        print((constants._PROGRESS_BAR_DESC_LENGTH+constants._PROGRESS_BAR_LENGTH)*"-"+"╮")

def _print_footer(export_data, endtime, starttime):
    """Print footer.
    """
    if not settings.silent:
        print((constants._PROGRESS_BAR_DESC_LENGTH+constants._PROGRESS_BAR_LENGTH)*"-"+"╯")
        if export_data:
            print("Data exported to "+settings.export_path['results'])
        if export_data or export_plots:
            print((constants._PROGRESS_BAR_DESC_LENGTH+constants._PROGRESS_BAR_LENGTH)*"-")
        print("FINISHED IN " + str(datetime.timedelta(seconds = round(endtime - starttime))))
        print((constants._PROGRESS_BAR_DESC_LENGTH+constants._PROGRESS_BAR_LENGTH)*"=")

def initialize_progress_bar(desc_string, total=1, unit="step"):
    """Initialize tqdm progress bar.
    """
    return tqdm(
        desc=("{:<"+str(constants._PROGRESS_BAR_DESC_LENGTH)+"}").format(desc_string),
        total=total,
        unit=unit,
        bar_format='{l_bar}{bar:'+str(constants._PROGRESS_BAR_LENGTH-7)+'}{r_bar}',
        disable=settings.silent,
    )

def import_network(street_network):
    """Import and project a street network from gpkg file

    For all edges between a pair of nodes u and v there must be one edge with key 0.

    Parameters
    ----------
    street_network : str
        The street network will be loaded from this file. Must be a gpkg file in unprojected crs EPSG:4326 with layers nodes and edges, with the structure that a osmnx street network g has after saving its undirected version via ox.io.save_graph_geopackage(). For example:
        >>> g = ox.graph_from_place("Barcelona", network_type='all_public', simplify=False, retain_all=True)
        >>> ox.io.save_graph_geopackage(g, "Barcelona_streets.gpkg")

    Returns
    -------
    nodes : geopandas.geodataframe.GeoDataFrame
        Extracted OSM nodes, projected
    edges : geopandas.geodataframe.GeoDataFrame
        Extracted OSM edges, projected
    g_undir : networkx.classes.multigraph.MultiGraph
        Extracted networkX graph, undirected
    city_boundary_gdf : geopandas.geodataframe.GeoDataFrame
        Convex hull of the street network
    """

    nodes = gpd.read_file(settings.import_path+street_network, layer='nodes')
    edges = gpd.read_file(settings.import_path+street_network, layer='edges')

    # Set indices as required by osmnx.convert.graph_from_gdfs
    # See: https://osmnx.readthedocs.io/en/stable/user-reference.html#osmnx.utils_graph.graph_from_gdfs
    nodes = nodes.set_index(['osmid'])
    edges = edges.set_index(['u', 'v', 'key'])

    g = ox.convert.graph_from_gdfs(nodes, edges)

    #city_boundary_gdf = gpd.GeoDataFrame(gpd.GeoSeries(nodes.union_all().convex_hull), geometry=0, crs=nodes.crs) # We do this before the projection of nodes below
    # To do: To be super-correct, the hull should be buffered by settings.seed_point_snap_distance (in degrees due to being unprojected)

    return g

def import_bike_network(bike_network, import_path=settings.import_path):
    """Import and project a street network from gpkg file

    For all edges between a pair of nodes u and v there must be one edge with key 0.

    Parameters
    ----------
    bike_network : str
        The street network will be loaded from this file. Must be a gpkg file in unprojected crs EPSG:4326 with layers nodes and edges, with the structure that a osmnx street network g has after saving its undirected version via ox.io.save_graph_geopackage(). For example:
        >>> g = ox.graph_from_place("Barcelona", network_type='all_public', simplify=False, retain_all=True)
        >>> g = nx.MultiGraph(ox.convert.to_digraph(g))
        >>> ox.io.save_graph_geopackage(g, "Barcelona_streets.gpkg")
    import_path : str, default settings.import_path
        Path to import files.

    Returns
    -------
    h: networkx.Graph
        graph of the bike network
    """

    nodes = gpd.read_file(import_path+bike_network, layer='nodes')
    edges = gpd.read_file(import_path+bike_network, layer='edges')

    # Set indices as required by osmnx.convert.graph_from_gdfs
    # See: https://osmnx.readthedocs.io/en/stable/user-reference.html#osmnx.utils_graph.graph_from_gdfs
    nodes = nodes.set_index(['osmid'])
    edges = edges.set_index(['u', 'v', 'key'])

    h = ox.convert.graph_from_gdfs(nodes, edges)

    #city_boundary_gdf = gpd.GeoDataFrame(gpd.GeoSeries(nodes.union_all().convex_hull), geometry=0, crs=nodes.crs) # We do this before the projection of nodes below
    # To do: To be super-correct, the hull should be buffered by settings.seed_point_snap_distance (in degrees due to being unprojected)

    return h

def resolve_crs_calculations(gdf, crs_projected=settings.crs_projected):
    """ Resolve settings.crs_projected = 'auto'

    Parameters
    ----------
    gdf : geopandas.geodataframe.GeoDataFrame
        A geodataframe from which to estimate the UTM CRS
    crs_projected : str
        A given CRS, or 'auto'. If 'auto', it is resolved to an estimated UTM.
        In this case, it also sets `settings.crs_projected` to the UTM.

    Returns
    -------
    crs_projected : str
        If it was set to 'auto', the estimated UTM, otherwise identical to the
        input `crs_calculations`.
    """
    if crs_projected == 'auto':
        crs_projected = gdf.estimate_utm_crs()
        settings.crs_projected = crs_projected
    return crs_projected

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
        if g.edges[edge].get("cycleway") in config.cycleway_bike_infra or g.edges[edge].get("cycleway:right") in config.cycleway_right_bike_infra or g.edges[edge].get("cycleway:left") in config.cycleway_left_bike_infra or g.edges[edge].get("cycleway:both") in config.cycleway_both_bike_infra or g.edges[edge].get("highway") in config.highway_bike_infra or g.edges[edge].get("cyclestreet") or g.edges[edge].get("bicycle_road") or g.edges[edge].get("highway") in config.highway_bike_infra_extended and g.edges[edge].get("bicycle") in config.bicycle_bike_infra and g.edges[edge].get("access") != 'private' and g.edges[edge].get("motor_vehicle") != 'yes':
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
    creates a geodataframe with edges attributes from a simple nx graph
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

def pair_between_largest_components(G, wcc):
    """Find the top `constants.TOP_CLOSEST_COMPONENTS` pairs of nodes 
    connecting the largest component to the second largest.

    Parameters
    ----------
    components : list of networkx.Graph
        Components sorted with the largest first.

    Returns
    -------
    closest_pairs : pandas.DataFrame
        The `constants.TOP_CLOSEST_COMPONENTS` candidates of node pairs, with 
        the following info: 'lcc_nodeid', 'comp_nodeid', 'distance_eucl', 
        'lcc', 'comp'
    """
    G1 = wcc[0]
    G2 = wcc[1]
    best_topn_distance = np.inf


    try: # Sanity check if connectable
        sp = nx.shortest_path(G, list(G1.nodes())[0], list(G2.nodes())[0])
    except nx.NetworkXNoPath:
        return None

    # Coordinates of nodes in the second component
    nodes2 = list(G2.nodes())
    coords2 = np.array([
        (G2.nodes[n]["x"], G2.nodes[n]["y"])
        for n in nodes2
    ])
    # Build KD-tree
    tree = cKDTree(coords2)

    closest_pairs = pd.DataFrame(columns=['lcc_nodeid','comp_nodeid','distance_eucl','lcc','comp'])
    # Query the nearest node in G2 for every node in G1
    for n1, data in G1.nodes(data=True):
        coord = np.array([data["x"], data["y"]])
        dist, idx = tree.query(coord)
        if len(closest_pairs) < constants.TOP_CLOSEST_COMPONENTS: # Start filling up
            closest_pairs.loc[len(closest_pairs)] = [n1, nodes2[idx], dist, G1, G2]
            closest_pairs.sort_values(by=['distance_eucl'], inplace=True)
            best_topn_distance = closest_pairs['distance_eucl'].iloc[-1]
        elif dist < best_topn_distance: # Append only if better than top N
            new_row = pd.DataFrame({
                'lcc_nodeid': [n1],
                'comp_nodeid': [nodes2[idx]],
                'distance_eucl': [dist],
                'lcc': [G1],
                'comp': [G2],
                })
            closest_pairs = pd.concat([closest_pairs, new_row]).reset_index(drop=True)
            closest_pairs = closest_pairs.nsmallest(constants.TOP_CLOSEST_COMPONENTS, 'distance_eucl')
            best_topn_distance = closest_pairs['distance_eucl'].iloc[-1]
    return closest_pairs.nsmallest(constants.TOP_CLOSEST_COMPONENTS,'distance_eucl') 

def get_underway_connections(H, pairinfo, components_sorted):
    """Taking a path between two components, get other components on the way 
    that also become connected.

    Parameters
    ----------
    H : networkx.Graph
        Graph of bicycle network components, connected up to a stage.
    pairinfo : pandas.DataFrame
        Data containing the closest node pair and more information: 
        'lcc_nodeid', 'comp_nodeid', 'distance_nw', 'path', 'lcc', 'comp'
    components_sorted : list of nx.Graph
        Connected components sorted with the largest first.

    Returns
    -------
    components_connected_underway : set
        Set of components that were connected underway. Can be empty.
    """
    components_connected_underway = set()
    for node in pairinfo['path']:
        if node in H:
            for component in components_sorted:
                if node in component:
                    components_connected_underway.add(component)
    return components_connected_underway

def pair_between_largest_and_closest_components(wcc):
    """Find the top `constants.TOP_CLOSEST_COMPONENTS` pairs of nodes 
    connecting the largest component to the geographically nearest remaining 
    components.

    Parameters
    ----------
    wcc : list of nx.Graph
        Connected components sorted with the largest first.

    Returns
    -------
    closest_pairs : pandas.DataFrame
        The `constants.TOP_CLOSEST_COMPONENTS` candidates of node pairs, with 
        the following info: 'lcc_nodeid', 'comp_nodeid', 'distance_eucl', 
        'lcc', 'comp'
    """
    lcc = wcc[0]

    # Build KD-tree for the largest component
    lcc_nodes = list(lcc.nodes())
    lcc_xy = np.array([
        (lcc.nodes[n]["x"], lcc.nodes[n]["y"])
        for n in lcc_nodes
    ])
    tree = cKDTree(lcc_xy)

    closest_pairs = pd.DataFrame(columns=['lcc_nodeid','comp_nodeid','distance_eucl','lcc','comp'])
    # Compare every remaining component to the lcc
    for comp in wcc[1:]:
        comp_nodes = list(comp.nodes())
        comp_xy = np.array([
            (comp.nodes[n]["x"], comp.nodes[n]["y"])
            for n in comp_nodes
        ])
        distances, indices = tree.query(comp_xy)
        i = np.argmin(distances)
        closest_pairs.loc[len(closest_pairs)] = [lcc_nodes[indices[i]], comp_nodes[i], distances[i], lcc, comp] # To do: Optimize. Never grow a dataframe. Could use code from pair_between_closest_components()
    return closest_pairs.nsmallest(constants.TOP_CLOSEST_COMPONENTS,'distance_eucl') 

def pair_between_closest_components(wcc):
    """Find the `constants.TOP_CLOSEST_COMPONENTS` closest pairs of nodes 
    belonging to two different connected components.

    Parameters
    ----------
    wcc : list of nx.Graph
        Connected components sorted with the largest first.

    Returns
    -------
    closest_pairs : pandas.DataFrame
        The `constants.TOP_CLOSEST_COMPONENTS` candidates of node pairs, with 
        the following info: 'lcc_nodeid', 'comp_nodeid', 'distance_eucl', 
        'lcc', 'comp'
    """
    closest_pairs = pd.DataFrame(columns=['lcc_nodeid','comp_nodeid','distance_eucl','lcc','comp'])
    best_topn_distance = np.inf

    for i in range(len(wcc) - 1):
        G1 = wcc[i]
        nodes1 = list(G1.nodes())
        coords1 = np.array([
            (G1.nodes[n]["x"], G1.nodes[n]["y"])
            for n in nodes1
        ])
        tree = cKDTree(coords1)

        # By construction, G1 is larger than G2
        for j in range(i + 1, len(wcc)):
            G2 = wcc[j]
            nodes2 = list(G2.nodes())
            coords2 = np.array([
                (G2.nodes[n]["x"], G2.nodes[n]["y"])
                for n in nodes2
            ])

            distances, indices = tree.query(coords2)
            k = np.argmin(distances)
            if len(closest_pairs) < constants.TOP_CLOSEST_COMPONENTS: # Start filling up
                closest_pairs.loc[len(closest_pairs)] = [nodes1[indices[k]], nodes2[k], distances[k], G1, G2]
                closest_pairs.sort_values(by=['distance_eucl'], inplace=True)
                best_topn_distance = closest_pairs['distance_eucl'].iloc[-1]
            elif distances[k] < best_topn_distance: # Append only if better than top N
                new_row = pd.DataFrame({
                    'lcc_nodeid': [nodes1[indices[k]]],
                    'comp_nodeid': [nodes2[k]],
                    'distance_eucl': [distances[k]],
                    'lcc': [G1],
                    'comp': [G2],
                    })
                closest_pairs = pd.concat([closest_pairs, new_row]).reset_index(drop=True)
                closest_pairs = closest_pairs.nsmallest(constants.TOP_CLOSEST_COMPONENTS, 'distance_eucl')
                best_topn_distance = closest_pairs['distance_eucl'].iloc[-1]
    return closest_pairs


def shortest_path_components_from_candidates(G, pair_candidates):
    """Given a set of node pair candidates between pairs of components, find
    the two components and their nodes that are closest.

    Parameters
    ----------
    G : networkx.Graph
        Graph for calculating shortest paths, with edges weighted via 'length'.
    pair_candidates : pandas.DataFrame
        Data set of node pair candidates between one lcc component and other
        components. Fields: 'lcc_nodeid', 'comp_nodeid'

    Returns
    -------
    closest_pairs : pandas.DataSeries
        Data containing the closest node pair and more information: 
        'lcc_nodeid', 'comp_nodeid', 'distance_nw', 'path', 'lcc', 'comp'
    """
    closest_pairs = pd.DataFrame(columns=['lcc_nodeid','comp_nodeid','distance_nw','path','lcc','comp'])
    for index, row in pair_candidates.iterrows():
        try:
            path_initial = nx.shortest_path(G, row['lcc_nodeid'], row['comp_nodeid'], weight='length')
            # We have so far only the shortest path between a pair of nodes 
            # between two components that have shortest euclidian distance. But 
            # there could be another pair of nodes between the two components 
            # that have shorter shortest paths. Find this node pair:
            path = shortest_path_components(G, [row['lcc'],row['comp']], path_initial)
            closest_pairs.loc[len(closest_pairs)] = [path[0], path[-1], float(nx.shortest_path_length(G, path[0], path[-1], weight='length')), path, row['lcc'],row['comp']]
        except nx.NetworkXNoPath:
            closest_pairs.loc[len(closest_pairs)] = [row['lcc_nodeid'], row['comp_nodeid'], np.inf, None, row['lcc'], row['comp']]
    return closest_pairs.nsmallest(1,'distance_nw').iloc[0]


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

def path_to_edges(nodelist):
    """Turn a list of nodes along a path into a list of edges along the path.

    Parameters
    ----------
    nodelist : list
        List of node ids, ordered along a path.

    Returns
    -------
    edgelist_final : list
        List of edge ids (=tuples of node ids), ordered along a path.
    """
    edgelist_prelim = zip(nodelist, nodelist[1:])
    edgelist_final = []
    for edge_prelim in edgelist_prelim:
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


def slugify(s):
    """Slugify a string

    Source: https://github.com/Chalarangelo/30-seconds-of-code/blob/master/content/snippets/python/s/slugify.md
    Note: A clean global solution would be using unidecode, but we do not want extra dependencies for this. We assume European city names in latin alphabet, some special letters like Hungarian long ö already mapped.

    Parameters
    ----------
    s : str
        String to slufigy

    Returns
    -------
    s : str
        Slugified string
    """
    s = s.lower().strip()
    s = re.sub(r'[\s-]+', '', s)  # Remove white spaces, -
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'^-+|-+$', '', s)
    tab = str.maketrans(
        "áéíóúàèìùòâêîôûäëïöüǎěǐǒǔãẽĩõũăåæçčıłñňøœřßșşšůŷÿźž",
        "aeiouaeiouaeiouaeiouaeiouaeiouaaaccilnnoorssssuyyzz"
    )
    s = s.translate(tab)
    return s

def calculate_network_statistics(H):
    """Return total network length and largest component length.

    Parameters
    ----------
    H: networkx.Graph
        undirected simple graph representing the street network with weighted edges

    Returns
    -------
    total_length: float
        total length of the network
    largest_length: float
        length of the largest connected component
    """

    total_length = sum(
        data["length"]
        for _, _, data in H.edges(data=True)
    )
    components = nx.connected_components(H)

    largest_component = max(components, key=lambda c: sum(
        H[u][v]["length"]
        for u, v in H.subgraph(c).edges()
    ))

    largest_length = sum(
        data["length"]
        for _, _, data in H.subgraph(largest_component).edges(data=True)
    )

    return total_length, largest_length

def mark_joined_component(H, component, step):
    """Mark components when they join the largest connected component
    
    Parameters
    ----------
    H: networkx.Graph
        undirected simple graph representing the street network with weighted edges
    component: networkx.Graph
        undirected simple graph representing a component of the existing bike network
    step: int
        the step at which the component is connected to the largest connected component
    """
    for u, v in H.subgraph(component).edges():
        H[u][v]["lcc_step"] = step

def shortest_path_components(G, pair_components, path):
    """Starting from an initial shortest path between a pair of nodes in two 
    different components, identify the two nodes and their shortest path which
    is truly the shortest path between the two components.
    
    Parameters
    ----------
    G : networkx.Graph
        Undirected simple graph representing the street network with weighted edges.
    pair_components : list
        Pair of networkx graph components. 
    path : list
        List of node ids making up the shortest path of two nodes from the two 
        components.
    
    Returns
    -------
    path : list
        List of node ids making up the shortest path between the two components.

    """
    u = dict(pair_components[0].nodes(data=False))
    v = dict(pair_components[1].nodes(data=False))
    last_nodeindex_in_u = 0
    first_nodeindex_in_v = -1
    for i in range(len(path)): # Iterate from u's node
        if path[i] in u:
            last_nodeindex_in_u = i
        elif path[i] in v: # We have reached the other component
            first_nodeindex_in_v = i
            break
    return path[last_nodeindex_in_u:first_nodeindex_in_v+1]
