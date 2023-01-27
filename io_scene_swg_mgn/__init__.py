# MIT License
#
# Copyright (c) 2022 Nick Rafalski
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

bl_info = {
    'name': "SWG Animated Mesh (.mgn)",
    "author": "Nick Rafalski (bug fixes and Blender 3+ support)",
    "version": (1, 0, 2),
    "blender": (2, 81, 6),
    "location":"File > Import-Export",
    "description": "Import and Export SWG animated meshes(.mgn)",
    'category': "Import-Export",
    }
## Import modules
if "bpy" in locals():
    import imp
    imp.reload(iff_tools)
    imp.reload(mgn_tools)
    imp.reload(mgnimport)
    imp.reload(mgnexport)
    imp.reload(swg_types)
    imp.reload(vector3D)
    imp.reload(vertex_buffer_format)
else:    
    from . import iff_tools
    from . import mgn_tools
    from . import mgnimport
    from . import mgnexport
    from . import swg_types
    from . import vector3D
    from . import vertex_buffer_format

import bpy


from bpy.props import (
        BoolProperty,
        FloatProperty,
        StringProperty,
        EnumProperty,
        )

from bpy_extras.io_utils import (
        ExportHelper,
        orientation_helper,
        axis_conversion,
        )

class MGN_PT_import_option(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Options"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_mgn"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator


@orientation_helper(axis_forward='Z', axis_up='Y')
class ExportMGN(bpy.types.Operator, ExportHelper):
    '''Export MGN object'''
    bl_idname='export_scene.mgn'
    bl_label='Export Mgn'
    bl_options = {'PRESET'}

    bl_description = 'Export a SWG Animated Mesh.'

    filename_ext = ".mgn"
    filter_glob: StringProperty(
            default="*.mgn",
            options={'HIDDEN'},
            )

    #filepath = StringProperty(name="File Path", description="File path used for exporting the MGN file", maxlen=1024, default="", subtype='FILE_PATH')
    #tangents : BoolProperty(name='Calculate Tangents', description="Calculate tangent vectors.", default=True)
    option_skeleton : StringProperty(name='Skeleton File', description="Skeleton file this mesh references. Debug option", maxlen=1024, default='all_b')
    occlusion : BoolProperty(name='Include OZN & ZTO?', description="Add OZN & ZTO chunks?", default=True)
    oitldata : BoolProperty(name='Use OITL?', description="Select to use OITL instead of ITL", default=False)
    overwriteWarning : BoolProperty(name="Overwrite Existing File", default=True)
    global_scale: FloatProperty(
            name="Scale",
            min=0.01, max=1000.0,
            default=1.0,
            )

    def execute(self, context):
        from . import swg_types
        from . import nsg_iff
        from . import mgnexport
        from mathutils import Matrix
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "global_scale",
                                            "filter_glob",))
        global_matrix = (Matrix.Scale(self.global_scale, 4) @
                         axis_conversion(to_forward=self.axis_forward,
                                         to_up=self.axis_up,
                                         ).to_4x4())

        keywords["global_matrix"] = global_matrix
        exported = mgnexport.export_mgn(context, **keywords)
        if exported:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

    def draw(self, context):
        pass

class MGN_PT_export_option(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Options"
    bl_parent_id = "FILE_PT_operator"

    @classmethod

    
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_SCENE_OT_mgn"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        #layout.prop(operator, 'tangents')
        layout.prop(operator, 'option_skeleton')
        layout.prop(operator, 'occlusion')
        layout.prop(operator, 'oitldata')
        layout.prop(operator, 'overwriteWarning')


## function calls
def mgn_import(self, context):
    self.layout.operator(mgnimport.IMPORT_OT_galaxies_mgn.bl_idname, text="SWG Animated Meshes (.mgn)")

def mgn_export(self, context):
    self.layout.operator(ExportMGN.bl_idname, text="SWG Animated Meshes (.mgn)")


classes = {
    mgnimport.IMPORT_OT_galaxies_mgn,
    MGN_PT_export_option,
    ExportMGN,    
    MGN_PT_import_option,
}

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(mgn_import)
    bpy.types.TOPBAR_MT_file_export.append(mgn_export)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(mgn_import)
    bpy.types.TOPBAR_MT_file_export.remove(mgn_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
