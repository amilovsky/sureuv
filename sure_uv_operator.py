import logging
from typing import List, Tuple, Any
import numpy as np
from math import sin, cos, pi

import bpy
from bpy.types import Operator, Image
from bpy.props import (
    BoolProperty,
    BoolVectorProperty,
    FloatProperty,
    FloatVectorProperty,
    StringProperty,
    PointerProperty
)
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector

from .sure_uv_utils import (get_settings,
                            get_image_by_name,
                            get_box_project_matrices,
                            create_checker_material,
                            create_checker_image,
                            get_areas_by_type)


_logger = logging.getLogger(__name__)
_log = lambda: None
_log.output = _logger.debug
_log.error = _logger.error


def update_texture_image(self, context: Any) -> None:
    image_name = self.texture_image
    img = get_image_by_name(image_name)
    if not img or not img.size:
        return
    w, h = img.size[:]
    if w == 0 or h == 0:
        return
    self.texaspect = w / h


class OBJECT_OT_SureUVBoxMapping(Operator):
    bl_idname = 'object.sure_uv_box_mapping'
    bl_label = 'Box mapping'
    bl_description = 'Check mapping options in the left bottom corner of 3D View'
    bl_options = {'REGISTER', 'UNDO'}

    texture_image: StringProperty(name='Image', update=update_texture_image)
    size: FloatProperty(name='Size', default=1.0, precision=4,
                        description='Texture real size (image width = Size)')
    size_x2: BoolProperty(name='x2', description='Scale x2', default=False)
    size_x05: BoolProperty(name='x0.5', description='Scale x0.5', default=False)
    texaspect: FloatProperty(name='Texture aspect', default=1.0, precision=4,
                             description='Texture aspect')
    rot: FloatVectorProperty(name='XYZ Rotation',
                             description='Angles of rotation')
    offset: FloatVectorProperty(name='XYZ offset', precision=4)
    reset_size: BoolProperty(name='Reset Texture Size')
    reset_texaspect: BoolProperty(name='Reset Aspect')
    guess_texaspect: BoolProperty(name='Guess Aspect')
    reset_xyz_rot: BoolProperty(name='Reset XYZ Rotation')
    reset_xyz_offset: BoolProperty(name='Reset XYZ Offset')

    def draw(self, context):
        layout = self.layout
        img = get_image_by_name(self.texture_image)
        tex_filepath = '-- No texture is selected --' if img is None else img.filepath
        layout.label(text=f'Texture: {tex_filepath}')
        layout.prop_search(self, 'texture_image', bpy.data, 'images')

        layout.label(text='Size')
        row = layout.row()
        split = row.split(factor=0.5)
        split.prop(self, 'size', text='')
        row = split.row()
        row.prop(self, 'size_x2', expand=True, icon='ZOOM_IN')
        row.prop(self, 'size_x05', expand=True, icon='ZOOM_OUT')
        row.prop(self, 'reset_size', icon='LOOP_BACK', text='')

        split = layout.row()

        col = split.column()
        row = col.row()
        row.label(text='XYZ rotation')
        row.prop(self, 'reset_xyz_rot', text='', icon='LOOP_BACK')
        col.prop(self, 'rot', text='')

        col = split.column()
        row = col.row()
        row.label(text='XYZ offset')
        row.prop(self, 'reset_xyz_offset', text='', icon='LOOP_BACK')
        col.prop(self, 'offset', text='')

        layout.label(text='Texture Aspect')
        layout.prop(self, 'texaspect', text='')
        row = layout.row()
        row.prop(self, 'reset_texaspect', icon='FILE_IMAGE', expand=True)
        row.prop(self, 'guess_texaspect', icon='FILE_IMAGE', expand=True)

    def box_mapping(self):
        scene = bpy.context.scene
        obj = bpy.context.object
        mesh = obj.data
        in_editmode = (obj.mode == 'EDIT')

        if in_editmode:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        if len(mesh.uv_layers) == 0:
            bpy.ops.mesh.uv_texture_add()

        matrices = get_box_project_matrices(self.size, self.texaspect,
                                            self.rot, self.offset)

        loop_vertex_indices = np.empty((len(mesh.loops),), dtype=np.int32)
        mesh.loops.foreach_get('vertex_index', loop_vertex_indices)

        mesh_verts = np.empty((len(mesh.vertices), 3), dtype=np.float32)
        mesh.vertices.foreach_get('co', mesh_verts.ravel())

        loop_verts = np.pad(mesh_verts[loop_vertex_indices], (0, 1),
                            'constant', constant_values=1)

        if in_editmode:
            selected_polygons = np.empty((len(mesh.polygons),), dtype=np.bool)
            mesh.polygons.foreach_get('select', selected_polygons)
            choice_indices = np.full((len(mesh.loops),), -1, dtype=np.int32)
        else:
            choice_indices = np.empty((len(mesh.loops),), dtype=np.int32)

        polygons = mesh.polygons if not in_editmode else \
            np.take(mesh.polygons, selected_polygons.nonzero()[0])

        for p in polygons:
            n = p.normal
            if abs(n[0]) > abs(n[1]) and abs(n[0]) > abs(n[2]):
                if n[0] >= 0:
                    choice = 0
                else:
                    choice = 1
            elif abs(n[1]) > abs(n[0]) and abs(n[1]) > abs(n[2]):
                if n[1] >= 0:
                    choice = 2
                else:
                    choice = 3
            else:
                if n[2] >= 0:
                    choice = 4
                else:
                    choice = 5
            choice_indices[p.loop_indices] = choice

        dir_indices = [(choice_indices == x).nonzero() for x in range(6)]

        uvmap = mesh.uv_layers.active.data
        new_uvs = np.empty((len(mesh.loops), 2), dtype=np.float32)

        if in_editmode:
            uvmap.foreach_get('uv', new_uvs.ravel())

        for i in range(6):
            new_uvs[dir_indices[i]] = loop_verts[dir_indices[i]] @ matrices[i].transpose()

        uvmap.foreach_set('uv', new_uvs.ravel())

        mesh.update()

        if in_editmode:
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    def invoke(self, context, event):
        _log.output('-- invoke Box mapping --')
        self.execute(context)
        _log.output('-- finish invoke --')
        return {'FINISHED'}

    def execute(self, context):
        _log.output('-- execute Box mapping --')
        _log.output(f'texture_image: {self.texture_image}')
        if self.size_x2:
            self.size_x2 = False
            self.size = self.size * 2.0
        if self.size_x05:
            self.size_x05 = False
            self.size = self.size * 0.5
        if self.reset_size:
            self.reset_size = False
            self.size = 1.0
        if self.reset_texaspect:
            self.reset_texaspect = False
            self.texaspect = 1.0
        if self.reset_xyz_offset:
            self.reset_xyz_offset = False
            self.offset = (0.0, 0.0, 0.0)
        if self.reset_xyz_rot:
            self.reset_xyz_rot = False
            self.rot = (0.0, 0.0, 0.0)
        if self.guess_texaspect:
            self.guess_texaspect = False
            update_texture_image(self, None)
        self.box_mapping()
        _log.output('-- finish execute --')
        return {'FINISHED'}


class OBJECT_OT_SureUVPlanarMapping(Operator):
    bl_idname = 'object.sure_uv_planar_mapping'
    bl_label = 'Best Planar mapping'
    bl_description = 'Mapping for selected polygons in EDIT Mode. ' \
                     'Check mapping options in the left bottom corner of 3D View'
    bl_options = {'REGISTER', 'UNDO'}

    texture_image: StringProperty(name='Image', update=update_texture_image)
    size: FloatProperty(name='Size', default=1.0, precision=4,
                        description='Texture real size (image width = Size)')
    size_x2: BoolProperty(name='x2', description='Scale x2', default=False)
    size_x05: BoolProperty(name='x0.5', description='Scale x0.5', default=False)
    texaspect: FloatProperty(name='Texture aspect', default=1.0, precision=4,
                             description='Texture aspect')
    zrot: FloatProperty(name='Z rotation', default=0.0,
                        description='Angle of rotation')
    xoffset: FloatProperty(name='X offset', default=0.0, precision=4,
                           description='X offset ')
    yoffset: FloatProperty(name='Y offset', default=0.0, precision=4,
                           description='Y offset')
    reset_size: BoolProperty(name='Reset Texture Size')
    reset_texaspect: BoolProperty(name='Reset Aspect')
    guess_texaspect: BoolProperty(name='Guess Aspect')
    reset_xoffset: BoolProperty(name='Reset X Offset')
    reset_yoffset: BoolProperty(name='Reset Y Offset')
    rotate_cw: BoolProperty(name='Rotate CW',
                            description='Rotate texture on +45 degree (clockwise)')
    rotate_ccw: BoolProperty(name='Rotate CCW',
                             description='Rotate texture on -45 degree (counter-clockwise)')
    reset_zrot: BoolProperty(name='Reset rotation',
                             description='Reset rotation angles to zero')

    def draw(self, context):
        layout = self.layout
        img = get_image_by_name(self.texture_image)
        tex_filepath = '-- No texture is selected --' if img is None else img.filepath
        layout.label(text=f'Texture: {tex_filepath}')
        layout.prop_search(self, 'texture_image', bpy.data, 'images')
        layout.label(text='Size')
        row = layout.row()
        split = row.split(factor=0.5)
        split.prop(self, 'size', text='')
        row = split.row()
        row.prop(self, 'size_x2', expand=True, icon='ZOOM_IN')
        row.prop(self, 'size_x05', expand=True, icon='ZOOM_OUT')
        row.prop(self, 'reset_size', icon='LOOP_BACK', text='')

        layout.label(text='Z rotation')
        row = layout.row()
        row.prop(self, 'zrot', text='')
        row.prop(self, 'reset_zrot', text='', icon='LOOP_BACK', expand=True)

        row = layout.row()
        row.prop(self, 'rotate_ccw', text='-45 (CCW)',
                 expand=True, icon='LOOP_BACK')
        row.prop(self, 'rotate_cw', text='+45 (CW)',
                 expand=True, icon='LOOP_FORWARDS')

        layout.label(text='XY offset')
        col = layout.column()
        row = col.row()
        row.prop(self, 'xoffset', text="")
        row.prop(self, 'reset_xoffset', text='', icon='LOOP_BACK')
        row = col.row()
        row.prop(self, 'yoffset', text='')
        row.prop(self, 'reset_yoffset', text='', icon='LOOP_BACK')

        layout.label(text="Texture aspect")
        layout.prop(self, 'texaspect', text="")
        row = layout.row()
        row.prop(self, 'reset_texaspect', icon='FILE_IMAGE', expand=True)
        row.prop(self, 'guess_texaspect', icon='FILE_IMAGE', expand=True)

    def best_planar_mapping(self):
        obj = bpy.context.object
        mesh = obj.data

        in_editmode = (obj.mode == 'EDIT')

        if in_editmode:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        if not len(mesh.uv_layers) > 0:
            bpy.ops.mesh.uv_texture_add()

        selected_polygons = np.empty((len(mesh.polygons),), dtype=np.bool)
        mesh.polygons.foreach_get('select', selected_polygons)

        polygon_indices = selected_polygons.nonzero()[0]

        polygon_normals = np.empty((len(mesh.polygon_normals), 3), dtype=np.float32)
        mesh.polygon_normals.foreach_get('vector', polygon_normals.ravel())

        selected_normals = polygon_normals[selected_polygons]
        if len(polygon_indices) > 0:
            average_vec = Vector(np.average(selected_normals, axis=0))
        else:
            average_vec = Vector((0,0,1))

        zv = Vector((0,0,1))
        quat = average_vec.rotation_difference(zv).to_matrix()

        aspect = self.texaspect
        sc = 1.0 / self.size if self.size != 0 else 1.0
        sx, sy, sz = sc, sc, sc
        rz = self.zrot / 180 * pi

        cosrz = cos(rz)
        sinrz = sin(rz)

        mat = np.array([[sx * cosrz, -sy * sinrz, 0, self.xoffset],
                        [sx * aspect * sinrz, sy * aspect * cosrz, 0, self.yoffset]])

        uvmap = mesh.uv_layers.active.data
        new_uvs = np.empty((len(mesh.loops), 2), dtype=np.float32)
        uvmap.foreach_get('uv', new_uvs.ravel())

        polygons = mesh.polygons if not in_editmode else \
            np.take(mesh.polygons, polygon_indices)
        for pol in polygons:
            for loop in pol.loop_indices:
                v_idx = mesh.loops[loop].vertex_index
                co = quat @ mesh.vertices[v_idx].co
                vec = [*co, 1.0]
                new_uvs[loop] = vec @ mat.transpose()

        uvmap.foreach_set('uv', new_uvs.ravel())

        if in_editmode:
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    def invoke(self, context, event):
        _log.output('-- invoke Planar mapping --')
        self.execute(context)
        _log.output('-- finish invoke --')
        return {'FINISHED'}

    def execute(self, context):
        _log.output('-- execute Planar mapping --')
        _log.output(f'texture_image: {self.texture_image}')
        if self.size_x2:
            self.size_x2 = False
            self.size = self.size * 2.0
        if self.size_x05:
            self.size_x05 = False
            self.size = self.size * 0.5
        if self.reset_size:
            self.reset_size = False
            self.size = 1.0
        if self.reset_texaspect:
            self.reset_texaspect = False
            self.texaspect = 1.0
        if self.guess_texaspect:
            self.guess_texaspect = False
            update_texture_image(self, None)
        if self.rotate_cw:
            self.zrot += 45
            self.zrot = self.zrot if self.zrot <= 360.0 else self.zrot - 360.0
            self.rotate_cw = False
        if self.rotate_ccw:
            self.zrot += -45
            self.zrot = self.zrot if self.zrot >= -360.0 else self.zrot + 360.0
            self.rotate_ccw = False
        if self.reset_zrot:
            self.zrot = 0.0
            self.reset_zrot = False
        if self.reset_size:
            self.reset_size = False
            self.size = 1.0
        if self.reset_xoffset:
            self.reset_xoffset = False
            self.xoffset = 0.0
        if self.reset_yoffset:
            self.reset_yoffset = False
            self.yoffset = 0.0
        self.best_planar_mapping()
        _log.output('-- finish execute --')
        return {'FINISHED'}

class OBJECT_OT_SureUVShowTextures(Operator):
    bl_idname = 'object.sure_uv_show_textures'
    bl_label = 'Show textures'
    bl_description = 'Show textures in viewport'
    bl_options = {'REGISTER', 'UNDO'}

    mode: StringProperty(name='Visual style mode', default='MATERIAL')

    def draw(self, context):
        pass

    def act(self, context):
        areas = get_areas_by_type('VIEW_3D')
        for area in areas:
            area.spaces.active.shading.type = self.mode

    def invoke(self, context, event):
        self.act(context)
        return {'FINISHED'}

    def execute(self, context):
        _log.output('-- execute --')
        _log.output(f'action: {self.action}')
        scene = bpy.context.scene
        settings = scene.sure_uv_settings
        _log.output(settings.teximage)
        self.act(context)
        return {'FINISHED'}


class OBJECT_OT_SureUVCheckerMat(Operator):
    bl_idname = 'object.sure_uv_checker_mat'
    bl_label = 'Checker material'
    bl_description = 'Apply checker material to whole mesh'
    bl_options = {'REGISTER', 'UNDO'}

    template: StringProperty(default='UV_GRID')

    def draw(self, context):
        pass

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        obj = bpy.context.object
        if obj.type != 'MESH':
            return {'CANCELLED'}

        if self.template == 'UV_GRID':
            checker_image_name = 'sure_uv_grid_checker1'
            checker_mat_name = 'sure_uv_checker_mat1'
            checker_type = 'UV_GRID'
        else:
            checker_image_name = 'sure_uv_grid_checker2'
            checker_mat_name = 'sure_uv_checker_mat2'
            checker_type = 'COLOR_GRID'

        checker_image = create_checker_image(image_name=checker_image_name,
                                             generated_type=checker_type)
        mat = create_checker_material(mat_name=checker_mat_name,
                                      image_name=checker_image_name)
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        return {'FINISHED'}


class OBJECT_OT_SureUVPreviewMat(Operator):
    bl_idname = 'object.sure_uv_preview_mat'
    bl_label = 'Preview material'
    bl_description = 'Apply temporary preview material with the currently ' \
                     'selected Texture to a whole object or selected polygons'
    bl_options = {'REGISTER', 'UNDO'}

    image_name: StringProperty(default='')
    action: StringProperty(default='preview_mat')

    def draw(self, context):
        pass

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        obj = bpy.context.object
        if self.action == 'preview_mat':
            preview_mat_name = 'sure_uv_preview_mat'
            mat = create_checker_material(mat_name=preview_mat_name,
                                          image_name=self.image_name)
            obj.data.materials.clear()
            obj.data.materials.append(mat)
        elif self.action == 'temp_mat':
            temp_mat_name = 'sure_uv_tmp_mat'
            mat = create_checker_material(mat_name=temp_mat_name,
                                          image_name=self.image_name,
                                          unique_name=False)
            obj.data.materials.append(mat)
            mat_id = len(obj.data.materials) - 1
            in_editmode = (obj.mode == 'EDIT')

            if in_editmode:
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

            for p in obj.data.polygons:
                if p.select:
                    p.material_index = mat_id

            if in_editmode:
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        return {'FINISHED'}


class OBJECT_OT_SureUVLoadImage(Operator, ImportHelper):
    bl_idname = 'object.sure_uv_load_image'
    bl_label = 'Load Image'
    bl_description = 'Load a texture image into the scene. ' \
                     'It can be used for fast texturing'
    bl_options = {'REGISTER', 'UNDO'}

    filter_folder: BoolProperty(
        name='Filter folders',
        default=True,
        options={'HIDDEN'},
    )
    filter_image: BoolProperty(
        name='Filter image',
        default=True,
        options={'HIDDEN'},
    )

    def draw(self, context):
        pass

    def invoke(self, context, event):
        return super().invoke(context, event)

    def execute(self, context):
        img = bpy.data.images.load(self.filepath)
        settings = get_settings()
        settings.teximage = img
        return {'FINISHED'}


class OBJECT_OT_SureUVSelectPolygons(Operator):
    bl_idname = 'object.sure_uv_select_polygons'
    bl_label = 'Sure UV Select polygons'
    bl_description = 'Sure UV Select polygons operator'
    bl_options = {'REGISTER', 'UNDO'}

    action: StringProperty(default='MATERIAL')

    def draw(self, context):
        pass

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        try:
            if self.action == 'MATERIAL':
                bpy.ops.mesh.select_similar(type='MATERIAL')
            elif self.action == 'COPLANAR':
                bpy.ops.mesh.select_similar(type='COPLANAR')
        except Exception as err:
            self.report({'ERROR'}, str(err))
        return {'FINISHED'}


class OBJECT_OT_SureUVResetScale(Operator):
    bl_idname = 'object.sure_uv_reset_scale'
    bl_label = 'Sure UV Reset Scale'
    bl_description = 'Sure UV Reset Scale operator'
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        pass

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            return {'CANCELLED'}
        obj.scale = (1, 1, 1)
        return {'FINISHED'}
