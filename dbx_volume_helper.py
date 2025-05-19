"""
Backend helper functions for Databricks Unity Catalog volume operations using the Databricks Python SDK.
"""

from databricks.sdk import WorkspaceClient
from typing import List, Dict, Optional

# Initialize the Databricks SDK client (assumes environment variables or config file for auth)
dbx = WorkspaceClient(host="https://e2-dogfood-cleanroom-eng-us-west-2.staging.cloud.databricks.com/", token = "")

def list_volumes(catalog_name: str, schema_name: str, limit: int = 20) -> List[Dict]:
    """
    List up to `limit` Unity Catalog volumes in the given catalog and schema.
    Returns a list of volume metadata dicts.
    """
    volumes = []
    try:
        for v in dbx.volumes.list(catalog_name=catalog_name, schema_name=schema_name):
            volumes.append({
                'name': v.name,
                'catalog_name': v.catalog_name,
                'schema_name': v.schema_name,
                'comment': getattr(v, 'comment', None),
                'storage_location': getattr(v, 'storage_location', None),
                'volume_type': getattr(v, 'volume_type', None),
            })
            if len(volumes) >= limit:
                break
    except Exception as e:
        print(f"Error listing volumes for {catalog_name}.{schema_name}: {e}")
    return volumes

def list_files_in_volume(catalog_name: str, schema_name: str, volume_name: str, path: str = "/") -> List[Dict]:
    """
    List files and folders in a given volume and path.
    Args:
        catalog_name: The catalog name (e.g., 'main')
        schema_name: The schema name (e.g., 'default')
        volume_name: The volume name (e.g., 'my-volume')
        path: The path within the volume (default is root '/')
    Returns a list of file/folder metadata dicts.
    """
    print(f"[DEBUG] list_files_in_volume called with: catalog={catalog_name}, schema={schema_name}, volume={volume_name}, path={path}")
    files = []
    volume_path = f"/Volumes/{catalog_name}/{schema_name}/{volume_name}{path}" if path.startswith("/") else f"/Volumes/{catalog_name}/{schema_name}/{volume_name}/{path}"
    try:
        for item in dbx.files.list_directory_contents(volume_path):
            is_dir = getattr(item, 'is_directory', False)
            files.append({
                'path': item.path,
                'is_dir': is_dir,
                'file_size': getattr(item, 'file_size', None),
                'modification_time': getattr(item, 'modification_time', None),
            })
    except Exception as e:
        print(f"Error listing files in {volume_path}: {e}")
    print(f"[DEBUG] list_files_in_volume result: {files}")
    return files

def upload_file_to_volume(volume_full_name: str, dest_path: str, file_bytes: bytes) -> bool:
    """
    Upload a file to a given volume and path.
    Args:
        volume_full_name: The full name of the volume (e.g., 'catalog.schema.volume')
        dest_path: The destination path within the volume (e.g., '/myfolder/myfile.txt')
        file_bytes: The file content as bytes
    Returns True if upload succeeded, False otherwise.
    """
    # TODO: Implement using dbx.files.upload()
    raise NotImplementedError

def get_file_content(file_path: str) -> bytes | None:
    """
    Download and return the content of a file given its full absolute path (e.g., '/Volumes/catalog/schema/volume/file.txt').
    Args:
        file_path: The full absolute path to the file in the volume.
    Returns the file content as bytes, or None if download fails.
    """
    try:
        resp = dbx.files.download(file_path)
        return resp.contents.read()
    except Exception as e:
        print(f"Error downloading file {file_path}: {e}")
        return None

def list_catalogs() -> list[str]:
    """
    List all available Unity Catalog catalogs.
    Returns a list of catalog names.
    """
    try:
        return [c.name for c in dbx.catalogs.list()]
    except Exception as e:
        print(f"Error listing catalogs: {e}")
        return []

def list_schemas(catalog_name: str) -> list[str]:
    """
    List all schemas in a given catalog.
    Returns a list of schema names.
    """
    try:
        return [s.name for s in dbx.schemas.list(catalog_name=catalog_name)]
    except Exception as e:
        print(f"Error listing schemas for catalog {catalog_name}: {e}")
        return []
