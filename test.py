from dask_gateway import Gateway
import rioxarray
import numpy as np
import xarray as xr
import dask
import pystac
from loguru import logger

gateway = Gateway("http://localhost:8001")

logger.info("Procuring a new Dask cluster")

# Define cluster options with a custom worker container image
cluster_options = gateway.cluster_options()

#cluster_options['image'] = 'docker.io/library/worker:5ee153c-dirty'
cluster_options['worker_cores'] = 1
cluster_options['worker_cores_limit'] = 2
cluster_options['worker_memory'] = "2 G"
# Create a new cluster with the specified options
cluster = gateway.new_cluster(cluster_options)


#logger.info("Scaling cluster to 4 workers")
#cluster.scale(n=4)

logger.info("Adapting cluster: minimum=1, maximum=10")
cluster.adapt(minimum=1, maximum=10)
client = cluster.get_client()

logger.info(f"Cluster dashboard: {cluster.dashboard_link}")


def get_asset(item, common_name):
    """Returns the asset of a STAC Item defined with its common band name"""
    for _, asset in item.get_assets().items():
        if not "data" in asset.to_dict()["roles"]:
            continue

        eo_asset = pystac.extensions.eo.AssetEOExtension(asset)
        if not eo_asset.bands:
            continue
        for b in eo_asset.bands:
            if (
                "common_name" in b.properties.keys()
                and b.properties["common_name"] == common_name
            ):
                return asset


def normalized_difference(band1, band2):
    return (band1 - band2) / (band1 + band2)


item_url = "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_10TFK_20210713_0_L2A"

item = pystac.read_file(item_url)

href_red = get_asset(item, "red").get_absolute_href()
href_nir = get_asset(item, "nir").get_absolute_href()

red = (
    rioxarray.open_rasterio(href_red, chunks={"x": 2048, "y": 2048})
    .squeeze()
    .astype(np.int16)
)
nir = (
    rioxarray.open_rasterio(href_nir, chunks={"x": 2048, "y": 2048})
    .squeeze()
    .astype(np.int16)
)

ndvi = xr.apply_ufunc(
    normalized_difference,
    nir,
    red,
    dask="parallelized",
    output_dtypes=[np.float32],
)

ndvi = ndvi.rio.write_crs(red.rio.crs, inplace=True)
ndvi = ndvi.rio.set_spatial_dims("x", "y", inplace=True)

# Trigger the computation and save as GeoTIFF
logger.info("Computing and saving NDVI as GeoTIFF...")
dask.compute(
    ndvi.astype("float32").rio.to_raster("ndvi.tif"),
)
logger.info("NDVI done!")

logger.info("Shutting down cluster")

cluster.shutdown()
