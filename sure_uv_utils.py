from typing import Any, Optional
import numpy as np

import bpy
from bpy.types import Object


def get_obj_verts(obj: Object) -> np.ndarray:
    mesh = obj.data
    verts = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    mesh.vertices.foreach_get('co',
                              np.reshape(verts, len(mesh.vertices) * 3))
    return verts


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
    count = len(mesh.polygons)
    normals = np.empty((count, 3), dtype=np.float32)
    mesh.vertices.foreach_get('normal',
                              np.reshape(normals, count * 3))
    return normals


def get_obj_normals2(obj: Object) -> np.ndarray:
    mesh = obj.data
    count = len(mesh.polygon_normals)
    normals = np.empty((count, 3), dtype=np.float32)
    mesh.polygon_normals.foreach_get('vector',
                                     np.reshape(normals, count * 3))
    return normals


def to_homogeneous(np_arr: np.ndarray) -> np.ndarray:
    return np.pad(np_arr, (0, 1), 'constant', constant_values=1)


def get_settings():
    return bpy.context.scene.sure_uv_settings
