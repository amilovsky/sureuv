import bpy
from bpy.types import Operator


class OBJECT_PT_SureUVPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Sure UV 1.0"
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

        layout.operator(opname,text="Show textures", icon='MATERIAL').action='showtex'

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

        col = layout.column()
        col.scale_y = 0.75
        col.label(text='How to use:')
        col.label(text='1. Make material with ')
        col.label(text='the raster Texture')
        col.label(text='2. Select the Texture to determine')
        col.label(text='texture Aspect')
        col.label(text='3. Use the Box mapping ')
        col.label(text='on whole object')
        col.label(text='4. Use the Best Planar mapping')
        col.label(text='on selected faces')

        layout.prop(settings,'autotexaspect')

        sx, sy, sz = obj.scale
        if sx != 1 or sy != 1 or sz != 1:
            box = layout.box()
            col = box.column()
            col.scale_y = 0.75
            col.alert = True
            col.label(text='Object scale warning!', icon='ERROR')
            col.label(text='Object has a non standard scale.')
            col.label(text='It can lead to wrong texture ')
            col.label(text='size and placement.')
            col.label(text='You can fix it by applying the scale:')
            op = box.operator('object.transform_apply',
                              text='Apply Object Scale')
            op.location=False
            op.rotation=False
            op.scale=True
