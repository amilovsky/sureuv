from typing import Any
from bpy.types import Image, PropertyGroup
from bpy.props import PointerProperty, BoolProperty, FloatProperty


def update_teximage_func(self, context: Any) -> None:
    img = self.teximage
    if not img:
        return
    self.texaspect = img.size[0] / img.size[1] if img.size[1] != 0 else 1.0


class SureUVSettings(PropertyGroup):
    teximage: PointerProperty(name='Image', type=Image,
                                        update=update_teximage_func)
    autotexaspect: BoolProperty(name='Auto texture Aspect', default=True,
                                description='Automatically detect Texture '
                                            'Aspect when selecting a texture')
    texaspect: FloatProperty(name='Texture Aspect', default=1.0, precision=4)
