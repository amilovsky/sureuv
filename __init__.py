bl_info = {
    "name": "Sure UV Map v.0.6.1",
    "author": "Alexander Milovsky",
    "blender": (2, 80, 0),
    "location": "View 3D > UI tab (Press `N` to see the panel). Mapping parameters in Tool Properties (bottom left corner)",
    "description": "Box / Best Planar UV Map for material with textures",
    "warning": "",
    "category": "UV"
}

import bpy
from . sure_uv_panel import OBJECT_PT_SureUVPanel
from . sure_uv_operator import OBJECT_OT_SureUVOperator
from . sure_uv_settings import SureUVSettings

classes = (
    OBJECT_PT_SureUVPanel,
    OBJECT_OT_SureUVOperator,
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
