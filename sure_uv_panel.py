from bpy.types import Panel
from .sure_uv_utils import get_area_shading_mode


class OBJECT_PT_SureUVPanel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'Sure UV 1.0'
    bl_category = 'Sure UV Map'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def _draw_show_texture_mode(self, layout, context):
        mode = get_area_shading_mode(context)
        if mode != 'MATERIAL':
            op = layout.operator('object.sure_uv_show_textures',
                                 text='Show texture mode', icon='MATERIAL')
            op.mode = 'MATERIAL'
        else:
            op = layout.operator('object.sure_uv_show_textures',
                                 text='Revert surface mode',
                                 icon='SHADING_SOLID')
            op.mode = 'SOLID'

    def _draw_how_to_use(self, layout):
        col = layout.column()
        col.scale_y = 0.75
        col.label(text='How to use:')
        col.label(text='1. Make material with ')
        col.label(text='the raster Texture')
        col.label(text='2. Select the Texture to determine')
        col.label(text='texture Aspect')
        col.label(text='3. Use the Box mapping ')
        col.label(text='on a whole object')
        col.label(text='4. Use the Best Planar mapping')
        col.label(text='on selected faces')

    def _draw_checkers(self, layout):
        col = layout.column(align=True)
        col.label(text='Checker materials:')
        col.operator('object.sure_uv_checker_mat',
                     text='Checker mat #1 (gray)',
                     icon='MATERIAL').template = 'UV_GRID'

        col.operator('object.sure_uv_checker_mat',
                     text='Checker mat #2 (color)',
                     icon='MATERIAL').template = 'COLOR_GRID'

    def _draw_select_polygons(self, layout):
        col = layout.column(align=True)
        col.label(text='Select polygons:')
        op = col.operator('object.sure_uv_select_polygons',
                          text='Same material')
        op.action = 'MATERIAL'
        op = col.operator('object.sure_uv_select_polygons',
                          text='Coplanar polygons')
        op.action = 'COPLANAR'

    def _draw_scale_warning(self, layout, context):
        obj = context.object
        sx, sy, sz = obj.scale
        if sx != 1 or sy != 1 or sz != 1:
            box = layout.box()
            col = box.column(align=True)
            col.scale_y = 0.75
            col.alert = True
            col.label(text='Object scale warning!', icon='ERROR')

            col = box.column(align=True)
            col.scale_y = 0.75
            col.label(text='Object has a non-standard scale.')
            col.label(text='It can lead to wrong texture ')
            col.label(text='size and placement.')

            col = box.column(align=True)
            op = col.operator('object.transform_apply',
                              text='Apply Object Scale')
            op.location = False
            op.rotation = False
            op.scale = True

            col.operator('object.sure_uv_reset_scale',
                         text='Reset Object Scale')

            box.label(text=f'X: {sx:.3f} Y: {sy:.3f} Z: {sz:.3f}')

    def _draw_uv_mapping(self, layout, image_name):
        col = layout.column(align=True)
        col.label(text='UV Mapping:')
        col.operator('object.sure_uv_box_mapping',
                     text='UV Box Map').texture_image = image_name

        col.operator('object.sure_uv_planar_mapping',
                     text='Best Planar Map').texture_image = image_name


    def draw(self, context):
        scene = context.scene
        obj = context.object
        settings = scene.sure_uv_settings
        layout = self.layout

        self._draw_show_texture_mode(layout, context)


        col = layout.column(align=True)
        aspect = settings.texaspect if settings.texaspect != 0.0 else 1.0
        col.label(text='Texture aspect: {:.4}'.format(aspect))
        col.template_ID_preview(settings, 'teximage', rows=4, cols=6, hide_buttons=True)
        col.operator('object.sure_uv_load_image', text='Load image in scene',
                     icon='FILEBROWSER')

        image_name = settings.teximage.name if settings.teximage else ''

        col = layout.column(align=True)
        col.label(text='Assign preview material with texture:')
        row = col.row(align=True)
        op = row.operator('object.sure_uv_preview_mat',
                          text='Single', icon='NODE_MATERIAL')
        op.image_name = image_name
        op.action = 'preview_mat'
        op = row.operator('object.sure_uv_preview_mat',
                          text='Multiple', icon='MATERIAL')
        op.image_name = image_name
        op.action = 'temp_mat'

        # layout.prop(settings,'autotexaspect')
        self._draw_uv_mapping(layout, image_name)
        self._draw_select_polygons(layout)
        self._draw_scale_warning(layout, context)
        self._draw_checkers(layout)
        # self._draw_how_to_use(layout)
