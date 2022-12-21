#!/usr/bin/python3.10
# coding=utf-8
import pandas as pd
import geopandas
import matplotlib.pyplot as plt
import contextily as ctx
import sklearn.cluster
import numpy as np


# muzete pridat vlastni knihovny


def make_geo(df: pd.DataFrame) -> geopandas.GeoDataFrame:
    """
    Konvertovani dataframe do geopandas.GeoDataFrame se spravnym kodovani, smazani radku bez hodnot ve sloupcich d, e
    :param df: DataFrame ktery funkce spracovava
    :return: GeoDataFrame vytvoreny z df
    """
    df = df[(df['d'].notna() & df['e'].notna())]
    df['date'] = pd.to_datetime(df['p2a'])
    return geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df["d"], df["e"]), crs="EPSG:5514")


def plot_geo(gdf: geopandas.GeoDataFrame, fig_location: str = None,
             show_figure: bool = False):
    """
    Vykresleni grafu s nehodami s alkoholem pro roky 2018-2021
    :param gdf: GeoDataFrame ze ktereho bude vykreslen graf
    :param fig_location: string, obsahujici jmeno souboru, do ktereho bude graf ulozen (vychozi: None)
    :param show_figure: ma se graf zobrazit? (vychozi: False)
    """
    years = pd.date_range("2018", periods=4, freq="Y").year
    data = gdf.copy()
    data = data[(data["region"] == "JHM") & (data["p11"] >= 3)].to_crs("EPSG:3857")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(13, 10))
    y = 0
    for ax in (ax1, ax2, ax3, ax4):
        ax.set_xlim(data.total_bounds[0], data.total_bounds[2])
        ax.set_ylim(data.total_bounds[1], data.total_bounds[3])
        data[data["date"].dt.year == years[y]].plot(ax=ax, markersize=1,
                                                    color="tab:red").set(title=f'JHM kraj (%d)' % years[y])
        ctx.add_basemap(ax=ax, crs=data.crs.to_string(), source=ctx.providers.Stamen.TonerLite, alpha=0.9)
        ax.axis("off")
        y += 1

    fig.suptitle('Nehody s alkoholem', fontsize=18)
    if fig_location:
        fig.savefig(fig_location)

    if show_figure:
        plt.show()


def plot_cluster(gdf: geopandas.GeoDataFrame, fig_location: str = None,
                 show_figure: bool = False):
    """
    Vykresleni grafu s lokalitou vsech nehod v kraji shlukovanych do clusteru
    :param gdf: GeoDataFrame ze ktereho bude vykreslen graf
    :param fig_location: string, obsahujici jmeno souboru, do ktereho bude graf ulozen (vychozi: None)
    :param show_figure: ma se graf zobrazit? (vychozi: False)
    """
    data = gdf.copy()
    data = data[(data["region"] == "JHM") & ((data["p36"] == 1) | (data["p36"] == 2) |
                                             (data["p36"] == 3))].to_crs("EPSG:3857")

    coords = np.dstack([data.geometry.x, data.geometry.y]).reshape(-1, 2)

    # Zkouseno pro 10, 20 a 30 clusteru MiniBatchKMeans a Agglomerative clusteringu, moznost 10 clusteru zavrhnuta,
    # protoze oblasti jsou prilis velke, 30 clusteru melo male oblasti s hodne prilis podobnymi hodnotami, proto
    # zvoleno 20 clusteru, zvoleno aglomerativni shlukovani, protoze vetsi shluky nerozdelilo do vice skupin (Znojmo)
    # db = sklearn.cluster.MiniBatchKMeans(n_clusters=20).fit(coords)
    db = sklearn.cluster.AgglomerativeClustering(n_clusters=20).fit(coords)
    data['cluster'] = db.labels_
    data = data.dissolve(by='cluster', aggfunc={'p1': 'count'})

    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    data.plot(column='p1', ax=ax, markersize=1, legend=True)
    ctx.add_basemap(ax=ax, crs=data.crs.to_string(), source=ctx.providers.Stamen.TonerLite, alpha=0.9)

    ax.axis("off")
    fig.suptitle('Nehody v JHM kraji na silnicích 1., 2. a 3. třídy')
    fig.tight_layout()
    if fig_location:
        fig.savefig(fig_location)

    if show_figure:
        plt.show()


if __name__ == "__main__":
    # zde muzete delat libovolne modifikace
    gdf = make_geo(pd.read_pickle("accidents.pkl.gz"))
    # plot_geo(gdf, "geo1.png", True)
    plot_cluster(gdf, "geo2.png", True)
