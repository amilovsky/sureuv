from typing import Any, Optional, Tuple, List
import numpy as np
from math import sin, cos, pi

import bpy
from bpy.types import Object, Image, Material


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


def get_box_project_matrices(
        size: float, aspect: float,
        rotation: Tuple[float, float, float],
        offset: Tuple[float, float, float]) -> List[np.ndarray]:
    sc = 1.0 / size if size != 0 else 1.0

    sx = 1 * sc
    sy = 1 * sc
    sz = 1 * sc
    ofx, ofy, ofz = offset
    rx = rotation[0] * pi / 180.0
    ry = rotation[1] * pi / 180.0
    rz = rotation[2] * pi / 180.0

    crx = cos(rx)
    srx = sin(rx)
    cry = cos(ry)
    sry = sin(ry)
    crz = cos(rz)
    srz = sin(rz)
    ofycrx = ofy * crx
    ofzsrx = ofz * srx

    ofysrx = ofy * srx
    ofzcrx = ofz * crx

    ofxcry = ofx * cry
    ofzsry = ofz * sry

    ofxsry = ofx * sry
    ofzcry = ofz * cry

    ofxcry = ofx * cry
    ofzsry = ofz * sry

    ofxsry = ofx * sry
    ofzcry = ofz * cry

    ofxcrz = ofx * crz
    ofysrz = ofy * srz

    ofxsrz = ofx * srz
    ofycrz = ofy * crz

    matrices = []
    matrices.append(np.array([
        [0, crx * sy, srx * sz, -ofycrx - ofzsrx],
        [0, -aspect * srx * sy, aspect * crx * sz, ofysrx - ofzcrx]
    ]))
    matrices.append(np.array([
        [0, -crx * sy, srx * sz, ofycrx - ofzsrx],
        [0, aspect * srx * sy, aspect * crx * sz, -ofysrx - ofzcrx]
    ]))
    matrices.append(np.array([
        [-cry * sx, 0, sry * sz, ofxcry - ofzsry],
        [aspect * sry * sx, 0, aspect * cry * sz, -ofxsry - ofzcry]
    ]))
    matrices.append(np.array([
        [cry * sx, 0, sry * sz, -ofxcry - ofzsry],
        [-aspect * sry * sx, 0, aspect * cry * sz, ofxsry - ofzcry]
    ]))
    matrices.append(np.array([
        [crz * sx, srz * sy, 0, -ofxcrz - ofysrz],
        [-aspect * srz * sx, aspect * crz * sy, 0, ofxsrz - ofycrz]
    ]))
    matrices.append(np.array([
        [-crz * sx, -srz * sy, 0, ofxcrz - ofysrz],
        [-aspect * srz * sx, aspect * crz * sy, 0, -ofxsrz - ofycrz]
    ]))
    return matrices


def create_new_mat(mat_name: str) -> Material:
    new_mat = bpy.data.materials.new(mat_name)
    new_mat.use_nodes = True
    return new_mat


def get_shader_node(mat: Material, find_type: str) -> Optional[Any]:
    for node in mat.node_tree.nodes:
        if node.type == find_type:
            return node
    return None


def get_material_by_name(mat_name: str) -> Optional[Image]:
    if mat_name in bpy.data.materials.keys():
        return bpy.data.materials[mat_name]
    return None


def get_image_by_name(image_name: str) -> Optional[Image]:
    if image_name in bpy.data.images.keys():
        return bpy.data.images[image_name]
    return None


def create_checker_image(*, generated_type: str='COLOR_GRID',
                         image_name: str='sure_uv_grid_checker',
                         tex_size: int=2048) -> Image:
    tex = get_image_by_name(image_name)
    if tex is None:
        tex = bpy.data.images.new(image_name, tex_size, tex_size)
    tex.source = 'GENERATED'
    tex.scale(tex_size, tex_size)
    tex.generated_type = generated_type
    return tex


def create_checker_material(*, mat_name: str, image_name: str) -> Material:
    mat = get_material_by_name(mat_name)
    if mat is None:
        mat = create_new_mat(mat_name)
    mat.use_nodes = True

    mat.node_tree.nodes.clear()

    principled_node = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')

    output_node = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    output_node.location = (350, 0)

    tex = get_image_by_name(image_name)
    tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex_node.image = tex
    tex_node.location = (-350, 0)

    mat.node_tree.links.new(
        principled_node.outputs['BSDF'],
        output_node.inputs['Surface'])

    mat.node_tree.links.new(
        tex_node.outputs['Color'],
        principled_node.inputs['Base Color'])
    return mat
