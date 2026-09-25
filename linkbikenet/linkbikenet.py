# imports
from . import settings
import os
import osmnx as ox
import networkx as nx
import pandas as pd
import geopandas as gpd
from collections import defaultdict
from tqdm import tqdm
import time

from linkbikenet.functions import (
    initialize_progress_bar,
    import_network,
    import_bike_network,
    resolve_crs_calculations,
    map_edges_to_bike_infrastructure,
    find_edges_to_drop,
    graph_edges_to_gdf,
    pair_between_largest_components,
    pair_between_largest_and_closest_components,
    pair_between_closest_components,
    get_correct_edgetuples,
    create_gdf_with_geoms,
    slugify,
    calculate_network_statistics,
    mark_joined_component
    )

def linkbikenet(
        city_query,
        connection_strategy = "largest_to_second",
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

    progress_bar = initialize_progress_bar("Processing network", 2)
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
    progress_bar.close()

    # finding parallel edges and dropping them
    edges_to_drop = find_edges_to_drop(g)
    g.remove_edges_from(edges_to_drop)

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

    # computing all weakly connected components to find out how many there are. This informs the amount of loops later
    wcc = [H.subgraph(c).copy() for c in sorted(nx.connected_components(H), key=lambda c: sum(
        [l[-1] for l in H.subgraph(c).copy().edges.data('length')]), reverse=True)]

    # Nodes belonging to the original largest component
    main_component = set(wcc[0])

    # Mark all edges in the original largest component as step 0
    for u, v in H.subgraph(main_component).edges():
        H[u][v]["lcc_step"] = 0

    to_iterate = len(wcc) - 1
    closest_pairs = []
    step = 1

    progress_bar = initialize_progress_bar("Postprocess data", 5)
    # check which strategy was chosen and execute the corresponding algorithm
    if connection_strategy == "largest_to_second":
        for i in range(to_iterate):
            wcc = [H.subgraph(c).copy() for c in sorted(nx.connected_components(H), key=lambda c: sum(
                [l[-1] for l in H.subgraph(c).copy().edges.data('length')]), reverse=True)]
            pair = pair_between_largest_components(wcc)
            # Determine which components contain u and v
            component_u = next(c for c in wcc if pair[0] in c)
            component_v = next(c for c in wcc if pair[1] in c)
            u_in_main = pair[0] in main_component
            v_in_main = pair[1] in main_component
            closest_pairs.append(pair)
            H.add_edge(pair[0], pair[1], length=0, lcc_step=None)
            if u_in_main and not v_in_main:
                mark_joined_component(H, component_v, step)
                main_component.update(component_v)
                H[pair[0]][pair[1]]["lcc_step"] = step

            elif v_in_main and not u_in_main:
                mark_joined_component(H, component_u, step)
                main_component.update(component_u)
                H[pair[0]][pair[1]]["lcc_step"] = step
            step += 1

    elif connection_strategy == "largest_to_closest":
        for i in range(to_iterate):
            wcc = [H.subgraph(c).copy() for c in sorted(nx.connected_components(H), key=lambda c: sum(
                [l[-1] for l in H.subgraph(c).copy().edges.data('length')]), reverse=True)]
            pair = pair_between_largest_and_closest_components(wcc)
            # Determine which components contain u and v
            component_u = next(c for c in wcc if pair[0] in c)
            component_v = next(c for c in wcc if pair[1] in c)
            u_in_main = pair[0] in main_component
            v_in_main = pair[1] in main_component
            closest_pairs.append(pair)
            H.add_edge(pair[0], pair[1], length=0, lcc_step=None)
            if u_in_main and not v_in_main:
                mark_joined_component(H, component_v, step)
                main_component.update(component_v)
                H[pair[0]][pair[1]]["lcc_step"] = step

            elif v_in_main and not u_in_main:
                mark_joined_component(H, component_u, step)
                main_component.update(component_u)
                H[pair[0]][pair[1]]["lcc_step"] = step
            step += 1

    elif connection_strategy == "closest_components":
        for i in range(to_iterate):
            wcc = [H.subgraph(c).copy() for c in sorted(nx.connected_components(H), key=lambda c: sum(
                [l[-1] for l in H.subgraph(c).copy().edges.data('length')]), reverse=True)]
            pair = pair_between_closest_components(wcc)
            # Determine which components contain u and v
            component_u = next(c for c in wcc if pair[0] in c)
            component_v = next(c for c in wcc if pair[1] in c)
            u_in_main = pair[0] in main_component
            v_in_main = pair[1] in main_component
            closest_pairs.append(pair)
            H.add_edge(pair[0], pair[1], length=0, lcc_step=None)
            if u_in_main and not v_in_main:
                mark_joined_component(H, component_v, step)
                main_component.update(component_v)
                H[pair[0]][pair[1]]["lcc_step"] = step

            elif v_in_main and not u_in_main:
                mark_joined_component(H, component_u, step)
                main_component.update(component_u)
                H[pair[0]][pair[1]]["lcc_step"] = step
            step += 1
    progress_bar.update(1)
    # find paths between node pairs so we can generate geometries
    paths = []
    for pair in closest_pairs:
        try:
            path = nx.shortest_path(G, pair[0], pair[1], weight='length')
        except nx.NetworkXNoPath:
            continue
        paths.append(path)

    H.remove_edges_from(closest_pairs)
    edges_pbi_gdf = graph_edges_to_gdf(H)
    progress_bar.update(1)

    edges_gdf = graph_edges_to_gdf(G)
    df = pd.DataFrame()
    df['nodelist'] = paths

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

    for i in range(len(gdf)):
        H.add_edge(closest_pairs[i][0], closest_pairs[i][1], length=edge_lengths[i])
        total, largest = calculate_network_statistics(H)
        network_lengths.append(total)
        lcc_lengths.append(largest)

    gdf['network_length'] = network_lengths
    gdf['lcc_length'] = lcc_lengths

    # add initial row to represent state of network before links are added
    initial_row = {
        "nodelist": None,
        "edge_list": None,
        "geometry": None,
        "network_length": initial_network_length,
        "lcc_length": initial_lcc_length,
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
    gdf['lcc_share'] = gdf['lcc_share'].round(4)
    edges_pbi_gdf['length'] = edges_pbi_gdf['length'].astype(int)

    gdf['ordering'] = gdf.index
    progress_bar.update(1)
    progress_bar.close()

    #edges_pbi_gdf = edges_gdf[edges_gdf["pbi"] == 1]

    # Back to unprojected (potentially). No more calculations after here.
    gdf.to_crs(epsg=4326, inplace=True)
    if import_files['bike_network'] is not None:
        edges_pbi_gdf.set_crs(epsg=4326, allow_override=True, inplace=True)
    else:
        edges_pbi_gdf.to_crs(epsg=4326, inplace=True)

    # Generate export data filename
    if export_data:
        os.makedirs(settings.export_path, exist_ok=True)
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
            gdf.to_file(settings.export_path + export_data_filename, driver="GeoJSON", RFC7946="YES")
            progress_bar.update(1)
            edges_pbi_gdf.to_file(settings.export_path + slugify(city_string) + "-linkbikenet-" + connection_strategy + "-existing_bike_network.geojson", driver="GeoJSON", RFC7946="YES")
            progress_bar.update(1)
            city_boundary.to_file(settings.export_path + slugify(city_string) + "-linkbikenet-city_boundary.geojson", driver="GeoJSON", RFC7946="YES")
            progress_bar.update(1)
        elif export_file_format == "gpkg":
            progress_bar = initialize_progress_bar("Exporting data", 1, "file")
            gdf.to_file(settings.export_path + export_data_filename, driver="GPKG", layer="Identified links")
            edges_pbi_gdf.to_file(settings.export_path + export_data_filename, driver="GPKG", layer="Existing bike network",
                                  append=True)
            city_boundary.to_file(settings.export_path + export_data_filename, driver="GPKG", layer="City boundary",
                                  append=True)
            progress_bar.update(1)
        progress_bar.close()

    return gdf