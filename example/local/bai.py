import stackstac
import xarray as xr
import pystac
from rasterio.enums import Resampling
import rioxarray
from loguru import logger
from dask_gateway import Gateway
import traceback


def main():
    # Convert the STAC items to xarray DataArray using stackstac with chunks
    pre_fire_stack = stackstac.stack(
        [
            pystac.read_file(
                "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_10TFK_20210713_0_L2A"
            )
        ],
        assets=["B08", "B12"],  # NIR and SWIR bands
        resolution=10,
        resampling=Resampling.nearest,
        chunksize=(1, 1, 1024, 1024),
    )

    post_fire_stack = stackstac.stack(
        [
            pystac.read_file(
                "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2A_10TFK_20210718_0_L2A"
            )
        ],
        assets=["B08", "B12"],  # NIR and SWIR bands
        resolution=10,
        resampling=Resampling.nearest,
        chunksize=(1, 1, 1024, 1024),
    )

    pre_fire_stack = pre_fire_stack.assign_coords(band=["B08", "B12"])
    post_fire_stack = post_fire_stack.assign_coords(band=["B08", "B12"])

    # Ensure that the stacks have the same spatial dimensions
    pre_fire_stack = pre_fire_stack.sel(x=post_fire_stack.x, y=post_fire_stack.y)

    # Convert to xarray Datasets and chunk them
    pre_fire_ds = pre_fire_stack.to_dataset(dim="band").chunk(
        {"band": 1, "y": 1024, "x": 1024}
    )
    post_fire_ds = post_fire_stack.to_dataset(dim="band").chunk(
        {"band": 1, "y": 2048, "x": 2048}
    )

    # Compute the Normalized Burn Ratio (NBR)
    def compute_nbr(nir, swir):
        return (nir - swir) / (nir + swir)

    # Compute NBR for pre and post fire
    pre_fire_nbr = compute_nbr(pre_fire_ds["B08"], pre_fire_ds["B12"]).squeeze(
        "time", drop=True
    )
    post_fire_nbr = compute_nbr(post_fire_ds["B08"], post_fire_ds["B12"]).squeeze(
        "time", drop=True
    )

    # Compute the difference to get the burnt area intensity
    burnt_area_intensity = pre_fire_nbr - post_fire_nbr

    # Check the shape and dimensions before saving
    logger.info(f"Burnt area intensity shape: {burnt_area_intensity.shape}")
    logger.info(f"Burnt area intensity dims: {burnt_area_intensity.dims}")

    # Compute and save the result using Dask
    burnt_area_intensity = burnt_area_intensity.astype("float32")
    
    burnt_area_intensity = burnt_area_intensity.rio.write_crs(
        pre_fire_ds.rio.crs, inplace=True
    )
    burnt_area_intensity = burnt_area_intensity.rio.set_spatial_dims(
        "x", "y", inplace=True
    )
    # Save to a raster file
    logger.info("Writing the result to a COG file")
    burnt_area_intensity.rio.to_raster(
        "bai.tif",
        driver="COG",
        dtype="float32",
        compress="deflate",
        blocksize=256,
        overview_resampling=Resampling.nearest,
    )

if __name__ == "__main__":
    gateway = Gateway("http://localhost:8001")

    logger.info("Procuring a new Dask cluster")

    # Define cluster options with a custom worker container image
    cluster_options = gateway.cluster_options()
    cluster_options[
        "image"
    ] = "worker:3853d0ad064e3f6b76696a81c99148113b44ac297759843d4c302017d4abaf45"
    cluster_options["worker_cores"] = 0.5
    cluster_options["worker_cores_limit"] = 1
    cluster_options["worker_memory"] = "4 G"

    # Create a new cluster with the specified options
    cluster = gateway.new_cluster(cluster_options)

    try:
        logger.info("Adapting cluster: minimum=4, maximum=4")
        cluster.adapt(minimum=4, maximum=20)
        client = cluster.get_client()
        print(f"Dask Dashboard: {client.dashboard_link}")
        logger.info("Running the burned area intensity")
        main()
        logger.info("Burned area intensity computation completed successfully!")

    except Exception as e:
        logger.error("Failed to run the script: {}", e)
        logger.error(traceback.format_exc())

    finally:
        client.close()
        cluster.close()
        logger.info("Dask cluster closed and shutdown!")
