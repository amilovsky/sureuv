import bpy


def update_func(self, context):
    img = self['teximage']
    if img:
        self.texaspect = img.size[0] / img.size[1] if img.size[0] / img.size[1] else 1.0


class SureUVSettings(bpy.types.PropertyGroup):   
    teximage: bpy.props.PointerProperty(
        name="Image", 
        type=bpy.types.Image,
        update=update_func
    )
    autotexaspect: bpy.props.BoolProperty(name="Auto Aspect", default=True)
    texaspect: bpy.props.FloatProperty(name="Texture Aspect", default=1.0, precision=4)
