from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
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

    @staticmethod
    def gs_to_vsi_path(path: str) -> str:
        if path.startswith("gs://"):
            return "/vsigs/" + path[len("gs://") :]
        return path

    def ensure_local_data_file(self, *parts: str) -> Path:
        normalized = [part.strip("/") for part in parts if part]
        path = self.data_path(*normalized)
        if isinstance(path, Path):
            return path

        import gcsfs

        cache_path = self.project_dir / ".gcs_cache"
        for part in normalized:
            cache_path = cache_path / part

        if cache_path.exists():
            return cache_path

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        fs = gcsfs.GCSFileSystem()
        with fs.open(path, mode="rb") as src, cache_path.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        return cache_path

    def open_xarray_dataset(self, *parts: str):
        import xarray as xr

        path = self.data_path(*parts)
        if isinstance(path, Path):
            return xr.open_dataset(path)

        import gcsfs

        fs = gcsfs.GCSFileSystem()
        file_obj = fs.open(path, mode="rb")
        return xr.open_dataset(file_obj, engine="h5netcdf")
