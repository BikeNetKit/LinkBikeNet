# imports
import os
import osmnx as ox
import networkx as nx
import pandas as pd

from linkbikenet.functions import *

def linkbikenet(
        city_name,
        connection_strategy = "largest",
        proj_crs = "3857",
        export_data = True,
        export_file_format = "geojson",
        import_files={},
):
    """
    Creates links between components of bicycle networks in cities. How components are connected depends on the connection strategy that was chosen.
    Parameters
    ----------
    city_name : str
        name of the city that the analysis should be performed on
    connection_strategy : str, default="largest
        strategy to use for connecting between components. Default is "largest", other options are "largest-closest" and "closest"
    proj_crs : str, default '3857'
        coordinate reference system that is used to project osm data. Default is '3857' (WGS 84 / Pseudo-Mercator)
    export_data : bool, optional, default True
        If set to True, data will be saved to a file. The filename is [slug].gpkg, where slug is a string id made out of city_name
    export_file_format : str, optional, default "geojson"
        File format for the data export, relevant if export_data set to True. Default "geojson", also possible "gpkg". If exporting as geojson, generates extra files for street network and city boundary. If exporting as gkpg, these are added all in one file as extra layers.
    import_files: dict, default {}
        The following key:value entries can be set:
            "street_network" : str | None, default None
                If not set to None, the street network is loaded from this file. Must be a gpkg file in unprojected crs EPSG:4326 with layers nodes and edges, with the structure that an undirected osmnx street network g has after saved via ox.io.save_graph_geopackage(). For example:
                >>> ox.settings.useful_tags_way = ["highway", "cycleway", "cycleway:right", "cycleway:left", "cycleway:both", "cyclestreet"]
                >>> g = ox.graph_from_place("Barcelona", network_type='all_public', simplify=False, retain_all=True)
                >>> g = nx.MultiGraph(ox.convert.to_digraph(g))
                >>> ox.io.save_graph_geopackage(g, "Barcelona_streets.gpkg").
    Returns
    -------
    gdf: geopandas.GeoDataFrame
        geodataframe with the proposed links, ordered after strategy chosen
    """
    # check if user input is valid
    if type(city_name) != str:
        raise TypeError("city_name must be a string")
    if type(proj_crs) != str:
        raise TypeError("proj_crs must be a string")
    if connection_strategy != "largest" and connection_strategy != "largest-closest" and connection_strategy != "closest":
        raise TypeError("connection_strategy must be 'largest', 'largest-closest' or 'closest'")
    if type(export_data) is not bool:
        raise TypeError("export_data must be a boolean")
    if export_file_format != "geojson" and export_file_format != "gpkg":
        raise ValueError("export_file_format must be 'geojson' or 'gpkg'")


    if import_files['street_network'] is not None:
        print("Importing street network..")
        g = import_network(import_files['street_network'])

    else:
        ### downloading and preprocessing data from OSM
        print("Downloading OSM data..")

        ox.settings.useful_tags_way = ["highway", "cycleway", "cycleway:right", "cycleway:left", "cycleway:both",
                                       "cyclestreet"]

        # fetch street network from OSM
        g = ox.graph_from_place(
            city_name, network_type='all_public', simplify=False, retain_all=True
        )

    g = ox.simplify_graph(
        g,
        edge_attrs_differ=['cycleway', 'highway', 'cycleway:right', 'cycleway:left', 'cycleway:both'],
    )

    # project graph for distance calculations
    g = ox.project_graph(g, to_crs=proj_crs)

    # check which edges have existing bicycle infrastructure and assign "pbi = 1" to them, all other edges get "pbi = 0".
    g = map_edges_to_bike_infrastructure(g)

    # finding parallel edges and dropping them
    print("Dropping parallel edges..")
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

    H = G.edge_subgraph(edges).copy()

    # computing all weakly connected components to find out how many there are. This informs the amount of loops later
    wcc = [H.subgraph(c).copy() for c in sorted(nx.connected_components(H), key=lambda c: sum(
        [l[-1] for l in H.subgraph(c).copy().edges.data('length')]), reverse=True)]

    to_iterate = len(wcc) - 1
    closest_pairs = []

    # check which strategy was chosen and execute the corresponding algorithm
    print("Calculating links...")
    if connection_strategy == "largest":
        for i in range(to_iterate):
            wcc = [H.subgraph(c).copy() for c in sorted(nx.connected_components(H), key=lambda c: sum(
                [l[-1] for l in H.subgraph(c).copy().edges.data('length')]), reverse=True)]
            pair = pair_between_largest_components(wcc)
            closest_pairs.append(pair)
            H.add_edge(pair[0], pair[1], length=0)

    elif connection_strategy == "largest-closest":
        for i in range(to_iterate):
            wcc = [H.subgraph(c).copy() for c in sorted(nx.connected_components(H), key=lambda c: sum(
                [l[-1] for l in H.subgraph(c).copy().edges.data('length')]), reverse=True)]
            pair = pair_between_largest_and_closest_components(wcc)
            closest_pairs.append(pair)
            H.add_edge(pair[0], pair[1], length=0)

    elif connection_strategy == "closest":
        for i in range(to_iterate):
            wcc = [H.subgraph(c).copy() for c in sorted(nx.connected_components(H), key=lambda c: sum(
                [l[-1] for l in H.subgraph(c).copy().edges.data('length')]), reverse=True)]
            pair = pair_between_closest_components(wcc)
            closest_pairs.append(pair)
            H.add_edge(pair[0], pair[1], length=0)

    # find paths between node pairs so we can generate geometries
    paths = []
    for pair in closest_pairs:
        try:
            path = nx.shortest_path(G, pair[0], pair[1], weight='length')
        except nx.NetworkXNoPath:
            continue
        paths.append(path)

    edges_gdf = graph_edges_to_gdf(G)
    df = pd.DataFrame()
    df['nodelist'] = paths

    df['edge_list'] = df.nodelist.apply(lambda x: get_correct_edgetuples(edges_gdf, x))
    gdf = create_gdf_with_geoms(df, edges_gdf)

    edges_pbi_gdf = edges_gdf[edges_gdf["pbi"] == 1]

    # Generate export data filename
    if export_data:
        os.makedirs("./results/", exist_ok=True)
        export_data_filename = (
                city_name + "." + export_file_format
        )

    if export_data:
        ### save data
        print("Saving data..")
        edges_pbi_gdf.drop(["osmid"], axis=1, inplace=True)
        city_boundary = ox.geocoder.geocode_to_gdf(city_name)
        city_boundary.to_crs(epsg=proj_crs, inplace=True)
        # We have meter precision, so rounding to integers is fine. Better would be to
        # change dtypes to int, but this does not seem possible without manual looping.
        city_boundary.geometry = city_boundary.geometry.set_precision(grid_size=1)
        edges_pbi_gdf.geometry = edges_pbi_gdf.geometry.set_precision(grid_size=1)
        gdf.geometry = gdf.geometry.set_precision(grid_size=1)
        if export_file_format == "geojson":
            gdf.to_file("./results/" + export_data_filename, driver="GeoJSON")
            edges_pbi_gdf.to_file("./results/" + city_name + "-existing_bike_network.geojson", driver="GeoJSON")
            city_boundary.to_file("./results/" + city_name + "-city_boundary.geojson", driver="GeoJSON")
        elif export_file_format == "gpkg":
            gdf.to_file("./results/" + export_data_filename, driver="GPKG", layer="Identified links")
            edges_pbi_gdf.to_file("./results/" + export_data_filename, driver="GPKG", layer="Existing bike network",
                                  append=True)
            city_boundary.to_file("./results/" + export_data_filename, driver="GPKG", layer="City boundary",
                                  append=True)

    return gdf