from typing import Any, Optional
import numpy as np

import bpy
from bpy.types import Object


def get_mesh_verts(mesh: Any) -> np.ndarray:
    verts = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    mesh.vertices.foreach_get('co', verts.ravel())
    return verts


def get_obj_verts(obj: Object) -> np.ndarray:
    return get_mesh_verts(obj.data)


def get_uvmap(obj: Object) -> Optional[Any]:
    mesh = obj.data
    if not mesh.uv_layers.active:
        return None
    return mesh.uv_layers.active.data


def get_uvs(obj: Object) -> np.ndarray:
    map = get_uvmap(obj)
    uvs = np.empty((len(map), 2), dtype=np.float32)
    map.foreach_get('uv', uvs.ravel())
    return uvs


def get_obj_normals(obj: Object) -> np.ndarray:
    mesh = obj.data
    normals = np.empty((len(mesh.polygons), 3), dtype=np.float32)
    mesh.vertices.foreach_get('normal', normals.ravel())
    return normals


def get_obj_normals2(obj: Object) -> np.ndarray:
    mesh = obj.data
    normals = np.empty((len(mesh.polygon_normals), 3), dtype=np.float32)
    mesh.polygon_normals.foreach_get('vector', normals.ravel())
    return normals


def to_homogeneous(np_arr: np.ndarray) -> np.ndarray:
    return np.pad(np_arr, (0, 1), 'constant', constant_values=1)


def get_settings():
    return bpy.context.scene.sure_uv_settings
