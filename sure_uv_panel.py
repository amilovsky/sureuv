import bpy
from bpy.types import Operator


class OBJECT_PT_SureUVPanel(bpy.types.Panel):
    bl_label = "Sure UV Mapping v.0.6.1"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Sure UV Addon"
    bl_category = "Sure UV Map"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def draw(self, context):
        # wm = context.window_manager
        scene = context.scene
        obj = context.object
        settings = scene.sure_uv_settings
        opname = 'object.sure_uv_operator'
        layout = self.layout

        aspect = settings.texaspect if settings.texaspect != 0.0 else 1.0

        layout.operator(opname,text="Show textures").action='showtex'

        layout.label(text="Texture aspect: {:.4}".format(settings.texaspect))
        layout.template_ID_preview(settings, "teximage", rows=4, cols=6, hide_buttons=True)

        layout.label(text="UV Mapping:")

        op = layout.operator(opname, text="UV Box Map")
        op.action='box'
        if settings.autotexaspect:
             op.texaspect = aspect

        op = layout.operator(opname, text="Best Planar Map")
        op.action='bestplanar'
        if settings.autotexaspect:
            op.texaspect = aspect

        layout.label(text="1. Make Material With Raster Texture")
        layout.label(text="2. Select Texture to determine TexAspect")        
        layout.label(text="3. Use Box mapping on whole object")
        layout.label(text="4. Use Best Planar on selected faces")

        layout.prop(settings,"autotexaspect")
