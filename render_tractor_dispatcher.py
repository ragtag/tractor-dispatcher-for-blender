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
Tractor Dispatcher is a simple tool for dispatching jobs to a render farm managed by Pixar's Tractor render manager.

HOW TO USE
Tractor Dispatcher only has a few settings, and will use whatever settings you've set in your .blend file to define everything else (output path and format of rendered images, start frame, end frame and so on).

OPTIONS
Render Scene - Check this scene if you want the scene to be rendered.
Frames Per Chunk - The number of frames to send to each tractor blade at a time.
Spool Path - This is where the .alf job script is saved, and a copy of your .blend file. This path needs to be accessible to all your tractor blades.
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
from bpy.props import IntProperty, StringProperty, BoolProperty

import os.path
import subprocess
from time import gmtime, strftime, sleep
from tempfile import gettempdir
from math import ceil

bpy.types.Scene.dorender = BoolProperty(
    name="Render Scene",
    description="Render the scene using current render settings",
    default=True
    )

#bpy.types.Scene.bakesim = BoolProperty(
#    name="Bake All Simulations",
#    description="Bake all simulations on a single farm node (not implemented)",
#    default=False
#    )

bpy.types.Scene.chunks = IntProperty(
    name="Frames Per Chunk", 
    description="Number of frames to run on each blade. Zero runs all on one blade",
    min = 1, max = 1000000,
    default = 1
    )

bpy.types.Scene.priority = IntProperty(
    name="Priority", 
    description="Priority in the tractor job queue",
    min = 0, max = 1000000,
    default = 1
    )

bpy.types.Scene.crews = StringProperty(
    name="Crews",
    description="Comma seperated list of crews to use",
    maxlen=4096,
    default=""
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
        #row.prop(sce, "bakesim")

        row =layout.row()
        row.prop(sce, "chunks")
        row.prop(sce, "priority")

        row = layout.row()
        row.prop(sce, "crews")

        row = layout.row()
        row.prop(sce, "spool")

        row = layout.row()
        row.operator("object.button", text="Batch", icon='BLENDER')


class OBJECT_OT_Button(bpy.types.Operator):
    bl_idname = "object.button"
    bl_label = "Button"
    bl_description = "Dispatch scene to tractor blades"
    mode = IntProperty(name="mode", default=1) 

    def execute(self, context):
        # Dispatch the job to tractor.
        # Spool out the blender file.
        if not os.path.exists(bpy.context.scene.spool):
            os.makedirs(bpy.context.scene.spool)
        spoolshort = "%s_%s.blend" % (os.path.basename(os.path.splitext(bpy.data.filepath)[0]), strftime("%y_%m_%d-%H_%M_%S", gmtime()))
        spoolfull = os.path.join(bpy.context.scene.spool, spoolshort)
        bpy.ops.wm.save_as_mainfile(filepath=spoolfull, copy=True)
        # Create the .alf script.
        jobshort = "%s_%s.alf" % (os.path.basename(os.path.splitext(bpy.data.filepath)[0]), strftime("%y_%m_%d-%H_%M_%S", gmtime()))
        jobfull = os.path.join(bpy.context.scene.spool, jobshort)
        self.file = open(jobfull, 'w')
        self.file.write("Job -title {%s} -priority %s -service {BlenderRender} -crews {%s} -envkey {} -subtasks {\n" % ( spoolshort, bpy.context.scene.priority, bpy.context.scene.crews ))
        start = bpy.context.scene.frame_start
        end = bpy.context.scene.frame_end
        fpc = bpy.context.scene.chunks # frames per chunk
        chunks = ceil(bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1)
        first  = start
        last = start + fpc -1
        for c in range(1,chunks):
            self.file.write("    Task {Range: %s,%s} -cmds {\n" % ( first, last))
            self.file.write("        RemoteCmd {blender --background %s --frame-start %s --frame-end %s --frame-jump 1 --render-anim} -tags {intensive}\n" % ( spoolfull, first, last ))
            self.file.write("    }\n")
            first = first + fpc
            last = last + fpc
            if first > end:
                break
            if last > end:
                last = end
        self.file.write("}")
        self.file.close()
        # Just to make doubly sure the .alf script is available on disk.
        sleep(1)
        # Dispatch the job to tractor.
        command = "tractor-spool.py %s" % (jobfull)
        #print(command)
        subprocess.call([ command, jobfull ], shell=True)
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
- See if it breaks with relative texture paths.
- Create more advanced .alf script, with progress and subtasks.
- Look at envkeys.
- Add Bake simulations (possibly try to split different sims on different nodes).
- Add custom icon of a tractor. :)
- Add support for running custom pre/post-script on the file and/or each chunk.
'''
