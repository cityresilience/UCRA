from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pandas as pd


@dataclass
class PipelineContext:
    project_dir: Path
    country: str
    crp_dir: Path
    aoi_folder: Path
    output_folder: Path
    cities: list[str]
    centroids: pd.DataFrame
    epsg_dict: dict
    gcs_data_bucket: str | None = None
    use_gcs_data: bool = False

    def data_path(self, *parts: str) -> str | Path:
        normalized = [part.strip("/") for part in parts if part]
        if self.use_gcs_data and self.gcs_data_bucket:
            return "/".join([self.gcs_data_bucket.rstrip("/")] + normalized)
        path = Path("data")
        for part in normalized:
            path = path / part
        return path

    def open_xarray_dataset(self, *parts: str):
        import xarray as xr

        path = self.data_path(*parts)
        if isinstance(path, Path):
            return xr.open_dataset(path)

        import gcsfs

        fs = gcsfs.GCSFileSystem()
        file_obj = fs.open(path, mode="rb")
        return xr.open_dataset(file_obj, engine="h5netcdf")
