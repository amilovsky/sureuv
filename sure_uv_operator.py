import numpy as np

import bpy
from bpy.types import Operator
from bpy.props import (
    BoolProperty,
    BoolVectorProperty,
    FloatProperty,
    FloatVectorProperty,
    StringProperty,
)
from math import sin, cos, pi
from mathutils import Vector

from .sure_uv_utils import get_settings, get_mesh_verts


class OBJECT_OT_SureUVOperator(bpy.types.Operator):
    """Sure UV Mapping"""
    bl_idname = "object.sure_uv_operator"
    bl_label = "Sure UV Operator"
    bl_options = {'REGISTER', 'UNDO'}

    action: StringProperty(name="String Value")
    size: FloatProperty(name="Size", default=1.0, precision=4)
    rot: FloatVectorProperty(name="XYZ Rotation")
    offset: FloatVectorProperty(name="XYZ offset", precision=4)

    zrot: FloatProperty(name="Z rotation", default=0.0)
    xoffset: FloatProperty(name="X offset", default=0.0, precision=4)
    yoffset: FloatProperty(name="Y offset", default=0.0, precision=4)
    texaspect: FloatProperty(name="Texture aspect", default=1.0, precision=4)
    
    reset_size: BoolProperty(name="Reset Size")
    reset_xoffset: BoolProperty(name="Reset X Offset")
    reset_yoffset: BoolProperty(name="Reset Y Offset")

    reset_xyz_rot: BoolProperty(name="Reset XYZ Rotation")
    reset_xyz_offset: BoolProperty(name="Reset XYZ Offset")

    reset_texaspect: BoolProperty(name="Reset Aspect")
    guess_texaspect: BoolProperty(name="Guess Aspect")

    flag_cw: BoolProperty()
    flag_ccw: BoolProperty()
    flag_zero: BoolProperty()

    def draw(self, context):
        if self.action == 'bestplanar':
            # self.action = 'bestplanar'
            layout = self.layout
            layout.label(text="Size")
            row = layout.row()
            row.prop(self,'size', text="")
            row.prop(self,'reset_size', icon="LOOP_BACK", text="")

            layout.label(text="Z rotation")
            row = layout.row()
            row.prop(self,'zrot',text="")
            row.prop(self,'flag_zero',text="", icon="LOOP_BACK")
            
            row = layout.row()
            row.prop(self,'flag_ccw',text="-45 (CCW)")
            row.prop(self,'flag_cw',text="+45 (CW)")
            
            layout.label(text="XY offset")
            col = layout.column()
            row = col.row()
            row.prop(self,'xoffset', text="")
            row.prop(self,'reset_xoffset',text="", icon="LOOP_BACK")
            row = col.row()
            row.prop(self,'yoffset', text="")
            row.prop(self,'reset_yoffset',text="", icon="LOOP_BACK")

            layout.label(text="Texture aspect")
            layout.prop(self,'texaspect', text="")
            row = layout.row()
            row.prop(self,'reset_texaspect')
            row.prop(self,'guess_texaspect')

        elif self.action == 'box':
            tex_name = '-- No texture is selected on sidebar --'
            settings = get_settings()
            if settings.teximage:
                tex_name = settings.teximage.name
            layout = self.layout
            layout.label(text=f'Texture: {tex_name}')
            layout.label(text="Size")
            row = layout.row()
            row.prop(self,'size', text="")
            row.prop(self,'reset_size', icon="LOOP_BACK", text="")

            split = layout.row()

            col = split.column()
            row = col.row()
            row.label(text="XYZ rotation")
            row.prop(self,'reset_xyz_rot',text="", icon="LOOP_BACK")
            col.prop(self,'rot', text="")

            col = split.column()
            row = col.row()
            row.label(text="XYZ offset")
            row.prop(self,'reset_xyz_offset',text="", icon="LOOP_BACK")
            col.prop(self,'offset', text="")

            layout.label(text="Texture Aspect")
            layout.prop(self,'texaspect', text="")
            row = layout.row()
            row.prop(self,'reset_texaspect')
            row.prop(self,'guess_texaspect')


    def act(self, context):
        if self.flag_cw:
            self.zrot += 45
            self.zrot = self.zrot if self.zrot <= 360.0 else self.zrot - 360.0
            self.flag_cw = False

        if self.flag_ccw:
            self.zrot += -45
            self.zrot = self.zrot if self.zrot >= -360.0 else self.zrot + 360.0
            self.flag_ccw = False

        if self.flag_zero:
            self.zrot = 0.0
            self.flag_zero = False

        if self.reset_size:
            self.reset_size = False
            self.size = 1.0

        if self.reset_xoffset:
            self.reset_xoffset = False
            self.xoffset = 0.0

        if self.reset_yoffset:
            self.reset_yoffset = False
            self.yoffset = 0.0

        if self.reset_xyz_offset:
            self.reset_xyz_offset = False
            self.offset = (0.0,0.0,0.0)

        if self.reset_xyz_rot:
            self.reset_xyz_rot = False
            self.rot = (0.0,0.0,0.0)

        if self.reset_texaspect:
            self.reset_texaspect = False
            self.texaspect = 1.0

        if self.guess_texaspect:
            self.guess_texaspect = False
            self.texaspect = context.scene.sure_uv_settings.texaspect

        if self.action == 'bestplanar':
            self.best_planar_map()
        
        elif self.action == 'box':
            self.box_map()
        
        elif self.action == 'doneplanar':
            self.best_planar_map()
        
        elif self.action == 'donebox':
            self.box_map()
        
        elif self.action == 'showtex':
            areas = context.workspace.screens[0].areas

            for area in areas:
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
    

    def invoke(self, context, event):
        # print('-- INVOKE --')
        # print(self.action)
        # print(self.texaspect)

        self.act(context)
            
        # print('-- finish invoke --')
        return {'FINISHED'}

    def execute(self, context):
        scene = bpy.context.scene
        settings = scene.sure_uv_settings

        # self.report({'INFO'}, 'S: {0}'.format(self.action))
        # print('Action:', self.action)

        self.act(context)
        return {'FINISHED'}

    def get_matrices(self):
        aspect = self.texaspect

        if self.size:
            sc = 1.0/self.size
        else:
            sc = 1.0   

        sx = 1 * sc
        sy = 1 * sc
        sz = 1 * sc
        ofx = self.offset[0]
        ofy = self.offset[1]
        ofz = self.offset[2]
        rx = self.rot[0] / 180 * pi
        ry = self.rot[1] / 180 * pi
        rz = self.rot[2] / 180 * pi
        
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
            [0, aspect * srx * sy, aspect * crx *sz, -ofysrx - ofzcrx]
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

    def box_map(self):
        scene = bpy.context.scene
        obj = bpy.context.object
        sure = scene.sure_uv_settings
        mesh = obj.data
        is_editmode = (obj.mode == 'EDIT')

        # if in EDIT Mode switch to OBJECT
        if is_editmode:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        # if no UVtex - create it
        if len(mesh.uv_layers) == 0:
            bpy.ops.mesh.uv_texture_add()

        matrices = self.get_matrices()

        #uvs = mesh.uv_loop_layers[mesh.uv_loop_layers.active_index].data
        uvs = mesh.uv_layers.active.data

        for i, pol in enumerate(mesh.polygons):
            if not is_editmode or mesh.polygons[i].select:
                for j, loop in enumerate(mesh.polygons[i].loop_indices):
                    v_idx = mesh.loops[loop].vertex_index
                    n = mesh.polygons[i].normal
                    co = mesh.vertices[v_idx].co
                    x = co.x
                    y = co.y
                    z = co.z
                    vec = np.array([x, y, z, 1])
                    if abs(n[0]) > abs(n[1]) and abs(n[0]) > abs(n[2]):
                        if n[0] >= 0:
                            uvs[loop].uv = matrices[0] @ vec
                        else:
                            uvs[loop].uv = matrices[1] @ vec
                    elif abs(n[1]) > abs(n[0]) and abs(n[1]) > abs(n[2]):
                        if n[1] >= 0:
                            uvs[loop].uv = matrices[2] @ vec
                        else:
                            uvs[loop].uv = matrices[3] @ vec
                    else:
                        if n[2] >= 0:
                            uvs[loop].uv = matrices[4] @ vec
                        else:
                            uvs[loop].uv = matrices[5] @ vec
        
        # Back to EDIT Mode
        if is_editmode:
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)


    # Best Planar Mapping
    def best_planar_map(self):        
        obj = bpy.context.object
        mesh = obj.data

        is_editmode = (obj.mode == 'EDIT')

        # if in EDIT Mode switch to OBJECT
        if is_editmode:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        # if no UVtex - create it
        if not len(mesh.uv_layers)>0:
            uvtex = bpy.ops.mesh.uv_texture_add()
        uvtex = mesh.uv_layers.active

        aspect = self.texaspect
                    
        #
        # Main action
        #
        if self.size:
            sc = 1.0/self.size
        else:
            sc = 1.0   

        # Calculate Average Normal
        v = Vector((0,0,0))
        cnt = 0
        for f in mesh.polygons:  
            if f.select:
                cnt += 1
                v = v + f.normal
        
        zv = Vector((0,0,1))
        q = v.rotation_difference(zv)
                

        sx = 1 * sc
        sy = 1 * sc
        sz = 1 * sc
        ofx = self.xoffset
        ofy = self.yoffset
        rz = self.zrot / 180 * pi

        cosrz = cos(rz)
        sinrz = sin(rz)

        #uvs = mesh.uv_loop_layers[mesh.uv_loop_layers.active_index].data
        uvs = mesh.uv_layers.active.data
        for i, pol in enumerate(mesh.polygons):
            if not is_editmode or mesh.polygons[i].select:
                for j, loop in enumerate(mesh.polygons[i].loop_indices):
                    v_idx = mesh.loops[loop].vertex_index

                    n = pol.normal
                    co = q @ mesh.vertices[v_idx].co
                    x = co.x * sx
                    y = co.y * sy
                    z = co.z * sz
                    uvs[loop].uv[0] =  x * cosrz - y * sinrz + self.xoffset
                    uvs[loop].uv[1] =  aspect*(- x * sinrz - y * cosrz) + self.yoffset

        # Back to EDIT Mode
        if is_editmode:
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)

