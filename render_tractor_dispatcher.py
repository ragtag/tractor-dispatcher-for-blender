# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

'''
DESCRIPTION
Tractor Dispatcher is a simple tool for dispatching jobs to a render farm managed by Pixar's Tractor render manager. It can be used both for rendering, and for running arbirarty batch jobs defined by a Python script. 

HOW TO USE
Tractor Dispatcher only has a few settings, and will use whatever settings you've set in your .blend file to define everything else (output path and format of rendered images, start frame, end frame and so on).

OPTIONS
Render Scene - Check this scene if you want the scene to be rendered.
Frames Per Chunk - The number of frames to send to each tractor blade at a time. If set to 0, the whole job will be sent to a single tractor blade, which is usefull for running simulations.
Spool Path - This is where the .alf job script is saved, and a copy of your .blend file. This path needs to be accessible to all your tractor blades.
Script: Python script to run on the scene. The script will be run once for each chunk. If Render Scene is checked, the script will be run before starting the render job.
'''

bl_info = {
    "name": "Tractor Dispatcher",
    "author": "Ragnar Brynjulfsson",
    "version": (0, 0, 0),
    "blender": (2, 6, 4),
    "location": "Properties > Render > Tractor Dispatcher",
    "description": "Dispatch jobs to Pixar's Tractor engine ",
    "warning": "Very much an alpah version",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"}

import bpy
from tempfile import gettempdir
from bpy.props import IntProperty, StringProperty, BoolProperty

bpy.types.Scene.dorender = BoolProperty(
    name="Render Scene",
    description="Render the scene using current render settings",
    default=True
    )

bpy.types.Scene.chunks = IntProperty(
    name="Frames Per Chunk", 
    description="Number of frames to run on each blade. Zero runs all on one blade",
    min = 0, max = 1000000,
    default = 1
    )

bpy.types.Scene.script = StringProperty(
    name="Script",
    description="Script to run for each chunk, leave empty if just rendering",
    maxlen=4096,
    default="",
    subtype='FILE_PATH'
    )

bpy.types.Scene.spool = StringProperty(
    name="Spool Path",
    description="Path to where temporary files are stored (.alf script and .blend file)",
    maxlen=4096,
    default=gettempdir(),
    subtype='DIR_PATH'
    )


class TractorDispatcherPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Tractor Dispatcher"
    bl_idname = "OBJECT_PT_tractor"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"


    def draw(self, context):
        layout = self.layout

        obj = bpy.context.active_object
        sce = bpy.context.scene

        row = layout.row()
        row.prop(sce, "dorender")
        row.prop(sce, "chunks")


        row = layout.row()
        row.prop(sce, "spool")

        row = layout.row()
        row.prop(sce, "script")

        row = layout.row()
        row.operator("object.button", text="Batch", icon='BLENDER')


class OBJECT_OT_Button(bpy.types.Operator):
    bl_idname = "object.button"
    bl_label = "Button"
    bl_description = "Dispatch scene to tractor blades"
    mode = IntProperty(name="mode", default=1) 

    def execute(self, context):
        print("Render")
        print(bpy.context.scene.dorender)
        print("Chunks")
        print(bpy.context.scene.chunks)
        print("Spool path")
        print(bpy.context.scene.spool)
        print("Python script to run")
        print(bpy.context.scene.script)
        return{'FINISHED'}    
        

def register():
    bpy.utils.register_class(OBJECT_OT_Button)
    bpy.utils.register_class(TractorDispatcherPanel)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_Button)
    bpy.utils.unregister_class(TractorDispatcherPanel)


if __name__ == "__main__":
    register()


'''
TODO!
- Save a copy of the blend file to the spool folder.
- Construct an .alf file.
- Run batch.
- Figure out how to filter by file types in the python script file browser.
- Create scripts for doing simulation (possibly add as checkbox feature).
- Add custom icon of a tractor. :)
'''
