bl_info = {
    "name": "Sure UV Map v.1.0.0",
    "version": (1, 0, 0),
    "author": "Alexander Milovsky",
    "blender": (2, 80, 0),
    "location": "View 3D > UI tab (Press N to see the panel)",
    "description": "Box / Best Planar UV Map for materials with textures",
    "doc_url": "https://github.com/amilovsky/sureuv",
    "tracker_url": "https://github.com/amilovsky/sureuv/issues",
    "category": "UV",
}


import bpy
from . sure_uv_panel import OBJECT_PT_SureUVPanel
from . sure_uv_operator import (OBJECT_OT_SureUVShowTexturesOperator,
                                OBJECT_OT_SureUVBoxMappingOperator,
                                OBJECT_OT_SureUVPlanarMappingOperator,
                                OBJECT_OT_SureUVCheckerMatOperator,
                                OBJECT_OT_SureUVPreviewMatOperator)
from . sure_uv_settings import SureUVSettings

classes = (
    OBJECT_PT_SureUVPanel,
    OBJECT_OT_SureUVShowTexturesOperator,
    OBJECT_OT_SureUVBoxMappingOperator,
    OBJECT_OT_SureUVPlanarMappingOperator,
    OBJECT_OT_SureUVCheckerMatOperator,
    OBJECT_OT_SureUVPreviewMatOperator,
    SureUVSettings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.sure_uv_settings = bpy.props.PointerProperty(
        type=SureUVSettings
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.sure_uv_settings
