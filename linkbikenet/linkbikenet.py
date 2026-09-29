# imports
from . import settings
from . import constants
import os
import osmnx as ox
import networkx as nx
import pandas as pd
import geopandas as gpd
from collections import defaultdict
from tqdm import tqdm
import time
pd.set_option('display.max_columns', None) # for debugging
import sys  # noqa: F401, use sys.exit() for debugging

from linkbikenet.functions import (
    initialize_progress_bar,
    import_network,
    import_bike_network,
    resolve_crs_calculations,
    map_edges_to_bike_infrastructure,
    find_edges_to_drop,
    get_underway_connections,
    graph_edges_to_gdf,
    pair_between_largest_components,
    pair_between_largest_and_closest_components,
    pair_between_closest_components,
    _print_footer,
    _print_header,
    get_correct_edgetuples,
    create_gdf_with_geoms,
    shortest_path_components,
    slugify,
    calculate_network_statistics,
    mark_joined_component,
    shortest_path_components_from_candidates,
    path_to_edges,
)

def linkbikenet(
    city_query,
    connection_strategy = "largest_to_closest",
    export_data = True,
    city_id = None,
    export_file_format = "geojson",
    import_files={},
):
    """
    Creates links between components of bicycle networks in cities. How components are connected depends on the connection strategy that was chosen.
    Parameters
    ----------
    city_query : str
        Search string for the city that the analysis should be performed on. This is the query used to fetch the data from nominatim.
    connection_strategy : str, default="largest
        strategy to use for connecting between components. Default is "largest_to_second", other options are "largest_to_closest" and "closest_components"
    export_data : bool, optional, default True
        If set to True, data will be saved to a file. The filename is [slug].gpkg, where slug is a string id made out of city_query
    city_id : str | None, default None
        If set, the slugified city_id is used in the filename of the data export. For example, a city_id "Athens" will slugify into "athens" in filenames. If set to None, the slugified city_query is used in the filename of the data export. It is useful to set a city_id for cities where the city_query is not the city name, for example to set for a city_query "Municipality of Athens" the city_id to "Athens".
    export_file_format : str, optional, default "geojson"
        File format for the data export, relevant if export_data set to True. Default "geojson", also possible "gpkg". If exporting as geojson, generates extra files for street network and city boundary. If exporting as gkpg, these are added all in one file as extra layers.
    import_files: dict, default {}
        The following key:value entries can be set:
            - 'city_boundary' : None or str, default None
            If not set to None, the study area is selected from the
            (Multi)Polygon provided in the city_boundary shape or gpkg file,
            ideally in unprojected latitude-longitude degrees (EPSG:4326), but
            EPSG:3857 also works.
            -"street_network" : str | None, default None
                If not set to None, the street network is loaded from this file. Must be a gpkg file in unprojected crs EPSG:4326 with layers nodes and edges, with the structure that an undirected osmnx street network g has after saved via ox.io.save_graph_geopackage(). For example:
                >>> ox.settings.useful_tags_way = ["highway", "cycleway", "cycleway:right", "cycleway:left", "cycleway:both", "cyclestreet"]
                >>> g = ox.graph_from_place("Barcelona", network_type='all_public', simplify=False, retain_all=True)
                >>> g = nx.MultiGraph(ox.convert.to_digraph(g))
                >>> ox.io.save_graph_geopackage(g, "Barcelona_streets.gpkg").
            "bike_network" : str | None, default None
                If not set to None, the existing bike network is loaded from this file. Must be a gpkg file in unprojected crs EPSG:4326 with layers nodes and edges, with the structure that an undirected osmnx bike network has after saved via ox.io.save_graph_geopackage().
    Returns
    -------
    gdf : geopandas.GeoDataFrame
        geodataframe with the proposed links, ordered after strategy chosen
    """
    # Setup
    starttime = time.time()

    # check if user input is valid
    if type(city_query) != str:
        raise TypeError("city_name must be a string")
    if connection_strategy != "largest_to_second" and connection_strategy != "largest_to_closest" and connection_strategy != "closest_components":
        raise TypeError("connection_strategy must be 'largest_to_second', 'largest_to_closest' or 'closest_components'")
    if type(export_data) is not bool:
        raise TypeError("export_data must be a boolean")
    if city_id is not None:
        if type(city_id) is not str:
            raise TypeError("city_id must be a string")
    if export_file_format != "geojson" and export_file_format != "gpkg":
        raise ValueError("export_file_format must be 'geojson' or 'gpkg'")
    if type(import_files) is not dict:
        raise TypeError("import_files must be a dictionary")
        # Prepare special case import_files. Turn it into a defaultdict where missing keys are None.
    import_files = defaultdict(lambda: None, import_files)

    _print_header(city_query, connection_strategy)

    # Get city boundary
    if import_files['city_boundary']:
        city_boundary_shp = gpd.read_file(settings.import_path + import_files['city_boundary'])
        city_boundary = city_boundary_shp.iloc[[0]]
    else:
        city_boundary = ox.geocoder.geocode_to_gdf(city_query)

    if import_files['bike_network'] is not None:
        progress_bar = initialize_progress_bar("Importing bike network data", 1, "network")
        h = import_bike_network(import_files['bike_network'])
        nodes_h = ox.graph_to_gdfs(h, nodes=True, edges=False, node_geometry=True)
        proj_crs = resolve_crs_calculations(nodes_h, settings.crs_projected)
        h = ox.project_graph(h, to_crs=proj_crs)
        h = nx.Graph(h)

    if import_files['street_network'] is not None:
        progress_bar = initialize_progress_bar("Importing bike network data", 1, "network")
        g = import_network(import_files['street_network'])

    else:
        ### downloading and preprocessing data from OSM
        progress_bar = initialize_progress_bar("Downloading OSM data", 1, "network")

        ox.settings.useful_tags_way = ["highway", "cycleway", "cycleway:right", "cycleway:left", "cycleway:both",
                                       "cyclestreet"]

        # fetch street network from OSM
        g = ox.graph_from_place(
            city_query, network_type='all_public', simplify=False, retain_all=True
        )
    progress_bar.update(1)
    progress_bar.close()

    progress_bar = initialize_progress_bar("Processing network", 3)
    g = ox.simplify_graph(
        g,
        edge_attrs_differ=['cycleway', 'highway', 'cycleway:right', 'cycleway:left', 'cycleway:both'],
    )

    # project graph for distance calculations
    nodes_g = ox.graph_to_gdfs(g, nodes=True, edges=False, node_geometry=True)
    proj_crs = resolve_crs_calculations(nodes_g, settings.crs_projected)
    g = ox.project_graph(g, to_crs=proj_crs)

    progress_bar.update(1)

    # check which edges have existing bicycle infrastructure and assign "pbi = 1" to them, all other edges get "pbi = 0".
    g = map_edges_to_bike_infrastructure(g)

    progress_bar.update(1)

    # progress_bar = initialize_progress_bar("Drop parallel edges")
    # # finding parallel edges and dropping them
    # edges_to_drop = find_edges_to_drop(g)
    # g.remove_edges_from(edges_to_drop)
    # progress_bar.update(1)
    # progress_bar.close()

    # Capital-G: the Graph() object we will be working with from now on
    G = nx.Graph(g)

    # build graph that only contains edges with protected bicycle infrastructure
    edges = [
        (u, v)
        for u, v, data in G.edges(data=True)
        if data.get("pbi") == 1
    ]

    if import_files['bike_network'] is not None:
        H = h.copy()
    else:
        H = G.edge_subgraph(edges).copy()

    # Compute all connected components and sort them by length, descending
    components_sorted = [H.subgraph(c).copy() for c in sorted(nx.connected_components(H), key=lambda c: sum(
        [l[-1] for l in H.subgraph(c).copy().edges.data('length')]), reverse=True)]

    # Nodes belonging to the original largest component
    main_component = set(components_sorted[0])

    # Mark all edges in the original largest component as step 0
    for u, v in H.subgraph(main_component).edges():
        H[u][v]["lcc_step"] = 0

    progress_bar.update(1)
    progress_bar.close()

    
    closest_pairs = []
    closest_components = []
    total = len(components_sorted)-1
    step = 1

    # check which strategy was chosen and execute the corresponding algorithm
    pathedges_all = set()
    paths_all = []
    num_comps_added = []
    comps_remaining = []
    if connection_strategy == "largest_to_second":
        progress_bar = initialize_progress_bar("Linking components", total, "component")
        for i in range(total):
            components_sorted = [H.subgraph(c).copy() for c in sorted(nx.connected_components(H), key=lambda c: sum(
                [l[-1] for l in H.subgraph(c).copy().edges.data('length')]), reverse=True)]
            if len(components_sorted) < 2:
                progress_bar.update(total-progress_bar.n)
                break
            comps_remaining.append(len(components_sorted))
            pair_candidates = pair_between_largest_components(G, components_sorted)
            if pair_candidates is None: # Completely disconnected - remove it
                for node in components_sorted[1]:
                    H.remove_node(node)
                continue
            pairinfo = shortest_path_components_from_candidates(G, pair_candidates)
            if pairinfo['path'] is None: # Completely disconnected - remove it
                for node in components_sorted[1]:
                    H.remove_node(node)
                continue
            pathedges = set(path_to_edges(pairinfo['path']))

            # Add unintended connections on the way
            components_connected_underway = get_underway_connections(H, pairinfo, components_sorted)
            num_comps_added.append(len(components_connected_underway)-1)
            progress_bar.update(len(components_connected_underway)-1)
            components_connected_underway.remove(components_sorted[0]) # Remove largest component
            components_connected_underway.remove(components_sorted[1]) # Remove second largest
            for c_underway in components_connected_underway: # Only add in-between components
                mark_joined_component(H, c_underway, step)

            # Add path
            paths_all.append(pairinfo['path'])
            G_path = G.subgraph(pairinfo['path']).copy()
            nx.set_edge_attributes(G_path, values=step, name="lcc_step")
            H = nx.compose(H, G_path)
            mark_joined_component(H, pairinfo['comp'], step)
            pathedges_all = pathedges_all.union(pathedges)
            step += 1
        progress_bar.close()

    elif connection_strategy == "largest_to_closest":
        for i in tqdm(
                range(total),
                desc=("{:<"+str(constants._PROGRESS_BAR_DESC_LENGTH)+"}").format("Linking components"),
                leave=True,
                unit="component",
                total=total,
                bar_format='{l_bar}{bar:'+str(constants._PROGRESS_BAR_LENGTH-7)+'}{r_bar}',
                disable=settings.silent,
            ):
            components_sorted = [H.subgraph(c).copy() for c in sorted(nx.connected_components(H), key=lambda c: sum(
                [l[-1] for l in H.subgraph(c).copy().edges.data('length')]), reverse=True)]
            pair_candidates = pair_between_largest_and_closest_components(components_sorted)
            if pair_candidates.isnull().values.all(): # Completely disconnected - ignore it
                continue
            pairinfo = shortest_path_components_from_candidates(G, pair_candidates)
            if pairinfo['path'] is None: # Completely disconnected - ignore it
                continue
            pathedges = path_to_edges(pairinfo['path'])
            paths_all.append(pairinfo['path'])
            G_path = G.subgraph(pairinfo['path']).copy()
            nx.set_edge_attributes(G_path, values=step, name="lcc_step")
            H = nx.compose(H, G_path)
            mark_joined_component(H, pairinfo['comp'], step)
            pathedges_all = pathedges_all.union(pathedges)
            num_comps_added.append(1)
            step += 1

    elif connection_strategy == "closest_components":
        for i in tqdm(
                range(total),
                desc=("{:<"+str(constants._PROGRESS_BAR_DESC_LENGTH)+"}").format("Linking components"),
                leave=True,
                unit="component",
                total=total,
                bar_format='{l_bar}{bar:'+str(constants._PROGRESS_BAR_LENGTH-7)+'}{r_bar}',
                disable=settings.silent,
            ):
            components_sorted = [H.subgraph(c).copy() for c in sorted(nx.connected_components(H), key=lambda c: sum(
                [l[-1] for l in H.subgraph(c).copy().edges.data('length')]), reverse=True)]
            pair_candidates = pair_between_closest_components(components_sorted)
            if pair_candidates.isnull().values.all(): # Completely disconnected - ignore it
                continue
            pairinfo = shortest_path_components_from_candidates(G, pair_candidates)
            if pairinfo['path'] is None: # Completely disconnected - ignore it
                continue
            pathedges = path_to_edges(pairinfo['path'])
            paths_all.append(pairinfo['path'])
            G_path = G.subgraph(pairinfo['path']).copy()
            nx.set_edge_attributes(G_path, values=step, name="lcc_step")
            H = nx.compose(H, G_path)
            mark_joined_component(H, pairinfo['comp'], step)
            pathedges_all = pathedges_all.union(pathedges)
            num_comps_added.append(1)
            step += 1

    progress_bar = initialize_progress_bar("Postprocessing data", 3)
    
    H.remove_edges_from(pathedges_all)
    edges_pbi_gdf = graph_edges_to_gdf(H)

  
    progress_bar.update(1)

    edges_gdf = graph_edges_to_gdf(G)
    df = pd.DataFrame()
    df['nodelist'] = paths_all

    df['edge_list'] = df.nodelist.apply(lambda x: get_correct_edgetuples(edges_gdf, x))
    gdf = create_gdf_with_geoms(df, edges_gdf)
    progress_bar.update(1)

    # reset Graph
    if import_files['bike_network'] is not None:
        H = h.copy()
    else:
        H = G.edge_subgraph(edges).copy()

    # calculating connectivity metrics
    network_lengths = []
    lcc_lengths = []
    edge_lengths = gdf['geometry'].length

    initial_network_length, initial_lcc_length = calculate_network_statistics(H)
    progress_bar.update(1)
    progress_bar.close()

    for i in tqdm( # To do: Optimize: Calculate already earlier instead of rebuilding the network.
            range(len(gdf)),
            desc=("{:<"+str(constants._PROGRESS_BAR_DESC_LENGTH)+"}").format("Calculating metrics"),
            leave=True,
            unit="component",
            total=len(gdf),
            bar_format='{l_bar}{bar:'+str(constants._PROGRESS_BAR_LENGTH-7)+'}{r_bar}',
            disable=settings.silent,
        ):
        G_path = G.subgraph(paths_all[i]).copy()
        H = nx.compose(H, G_path)
        total, largest = calculate_network_statistics(H)
        network_lengths.append(total)
        lcc_lengths.append(largest)
    progress_bar.close()

    gdf['network_length'] = network_lengths
    gdf['lcc_length'] = lcc_lengths
    gdf['link_length'] = edge_lengths
    gdf['num_components_added'] = num_comps_added

    # add initial row to represent state of network before links are added
    initial_row = {
        "nodelist": None,
        "edge_list": None,
        "geometry": None,
        "network_length": initial_network_length,
        "lcc_length": initial_lcc_length,
        "link_length": 0,
        "num_components_added": 0,
    }
    # Turn it into a one-row GeoDataFrame
    initial_gdf = gpd.GeoDataFrame(
        [initial_row],
        geometry="geometry",
        crs=gdf.crs
    )

    # Put step 0 at the beginning
    gdf = pd.concat(
        [initial_gdf, gdf],
        ignore_index=True
    )

    gdf['lcc_share'] = gdf['lcc_length'] / gdf['network_length']
    gdf['lcc_gain'] = gdf['lcc_length'].diff().fillna(0)

    # Round
    gdf['network_length'] = gdf['network_length'].astype(int)
    gdf['lcc_length'] = gdf['lcc_length'].astype(int)
    gdf['lcc_gain'] = gdf['lcc_gain'].astype(int)
    gdf['link_length'] = gdf['link_length'].astype(int)
    gdf['num_components_added'] = gdf['num_components_added'].astype(int)
    gdf['lcc_share'] = gdf['lcc_share'].round(4)
    edges_pbi_gdf['length'] = edges_pbi_gdf['length'].astype(int)

    gdf['ordering'] = gdf.index
    

    #edges_pbi_gdf = edges_gdf[edges_gdf["pbi"] == 1]

    # Back to unprojected (potentially). No more calculations after here.
    gdf.to_crs(epsg=4326, inplace=True)
    if import_files['bike_network'] is not None:
        edges_pbi_gdf.set_crs(epsg=4326, allow_override=True, inplace=True)
    else:
        edges_pbi_gdf.to_crs(epsg=4326, inplace=True)

    # Generate export data filename
    if export_data:
        os.makedirs(settings.export_path['results'], exist_ok=True)
        if city_id is None:
            city_string = city_query
        else:
            city_string = city_id
        export_data_filename = (
                slugify(city_string) + "-linkbikenet-" + connection_strategy + "." + export_file_format
        )

    if export_data:
        # Cleanup
        keepedgedata = ['length', 'lcc_step', 'geometry', 'u', 'v']
        for p in edges_pbi_gdf.keys():
            if p not in keepedgedata:
                del edges_pbi_gdf[p] 

        city_boundary.to_crs(epsg=4326, inplace=True)
        if export_file_format == "geojson":
            progress_bar = initialize_progress_bar("Exporting data", 3, "file")
            gdf.to_file(settings.export_path['results'] + export_data_filename, driver="GeoJSON", RFC7946="YES")
            progress_bar.update(1)
            edges_pbi_gdf.to_file(settings.export_path['results'] + slugify(city_string) + "-linkbikenet-" + connection_strategy + "-existing_bike_network.geojson", driver="GeoJSON", RFC7946="YES")
            progress_bar.update(1)
            city_boundary.to_file(settings.export_path['results'] + slugify(city_string) + "-linkbikenet-city_boundary.geojson", driver="GeoJSON", RFC7946="YES")
            progress_bar.update(1)
        elif export_file_format == "gpkg":
            progress_bar = initialize_progress_bar("Exporting data", 1, "file")
            gdf.to_file(settings.export_path['results'] + export_data_filename, driver="GPKG", layer="Identified links")
            edges_pbi_gdf.to_file(settings.export_path['results'] + export_data_filename, driver="GPKG", layer="Existing bike network",
                                  append=True)
            city_boundary.to_file(settings.export_path['results'] + export_data_filename, driver="GPKG", layer="City boundary",
                                  append=True)
            progress_bar.update(1)
        progress_bar.close()

    # Cleanup, finalize
    endtime = time.time()
    _print_footer(export_data, endtime, starttime)

    return gdf