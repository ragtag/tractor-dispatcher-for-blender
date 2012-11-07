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

You will need a tractor-spool.py in path, Tractor licenses and a renderfarm to use this script. All paths, including the spool path need to be accessible from all the render nodes.
'''

bl_info = {
    "name": "Tractor Dispatcher",
    "author": "Ragnar Brynjulfsson",
    "version": (0, 0, 1),
    "blender": (2, 6, 4),
    "location": "Properties > Render > Tractor Dispatcher",
    "description": "Dispatch jobs to Pixar's Tractor engine ",
    "warning": "Very much an alpah version",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"}

import bpy
from bpy.props import IntProperty, StringProperty, BoolProperty, FloatProperty

import os.path
import subprocess
from time import gmtime, strftime, sleep
from tempfile import gettempdir
from math import ceil

#bpy.types.Scene.bakesim = BoolProperty(
#    name="Bake All Simulations",
#    description="Bake all simulations on a single farm node (not implemented)",
#    default=False
#    )

#bpy.types.Scene.postbakescript = StringProperty(
#    name="Post-Bake Script",
#    description="Optional script to run after baking simulation, but before rendering",
#    maxlen=4096,
#    subtype='DIR_PATH'
#    )

bpy.types.Scene.dorender = BoolProperty(
    name="Render Scene",
    description="Render the scene using current render settings",
    default=True
    )

bpy.types.Scene.prescript = StringProperty(
    name="Pre-Script",
    description="Optional script file to run before the job starts",
    maxlen=4096,
    subtype='FILE_PATH'
    )

bpy.types.Scene.postscript = StringProperty(
    name="Post-Script",
    description="Optional script file to run after the job is done",
    maxlen=4096,
    subtype='FILE_PATH'
    )

bpy.types.Scene.priority = FloatProperty(
    name="Priority", 
    description="Priority in the tractor job queue",
    min = 0.0, max = 1000000.0,
    default = 1.0
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

bpy.types.Scene.doclean = BoolProperty(
    name="Clean Spool",
    description="Remove .alf job script and spooled .blend file once done (not implemented)",
    default=False
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
        # row.prop(sce, "bakesim")
        row.prop(sce, "doclean")

        row =layout.row()
        row.prop(sce, "priority")

        row = layout.row()
        row.prop(sce, "crews")
        row = layout.row()
        row.prop(sce, "spool")

        row = layout.row()
        row.prop(sce, "prescript")
        #row = layout.row()
        #row.prop(sce, "postbakescript")
        row = layout.row()
        row.prop(sce, "postscript")

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
        bpy.ops.wm.save_as_mainfile(filepath=spoolfull, copy=True, relative_remap=True)
        # Create the .alf script.
        jobshort = "%s_%s.alf" % (os.path.basename(os.path.splitext(bpy.data.filepath)[0]), strftime("%y_%m_%d-%H_%M_%S", gmtime()))
        jobfull = os.path.join(bpy.context.scene.spool, jobshort)
        self.file = open(jobfull, 'w')
        self.file.write("Job -title {%s} -priority %s -service {BlenderRender} -crews {%s} -envkey {} -serialsubtasks 1 -subtasks {\n" % ( spoolshort, bpy.context.scene.priority, bpy.context.scene.crews ))

        # Run pre-script, simulations and post-bake script.
        if bpy.context.scene.prescript:
            self.file.write("    Task {Pre-Job Script} -cmds {\n")
            self.file.write("        RemoteCmd {blender --background %s --python %s}\n" % ( spoolfull, bpy.context.scene.prescript ))
            self.file.write("    }\n")
        #if bpy.context.scene.bakesim:
        #    self.file.write("    Task {Bake All Simulations} -cmds {\n")
        #    self.file.write("        RemoteCmd {sleep 5}\n")
        #    self.file.write("    }\n")
        #if bpy.context.scene.postbakescript:
        #    self.file.write("    Task {Post-Bake Script} -cmds {\n")
        #    self.file.write("        RemoteCmd {blender --background %s --python %s}\n" % ( spoolfull, bpy.context.scene.postbakescript ))
        #    self.file.write("    }\n")

        # Render frames
        if bpy.context.scene.dorender:
            self.file.write("    Task {Render Frames} -subtasks {\n")
            start = bpy.context.scene.frame_start
            end = bpy.context.scene.frame_end + 1
            step = bpy.context.scene.frame_step
            for f in range(start,end,step):
                self.file.write("        Task {Frame %s} -cmds {\n" % ( f ))
                self.file.write("            RemoteCmd {blender --background %s --frame-start %s --frame-end %s --frame-jump 1 --render-anim} -tags {intensive}\n" % ( spoolfull, f, f ))
                self.file.write("        }\n")
            self.file.write("    }\n")

        # Run post-script
        if bpy.context.scene.postscript:
            self.file.write("    Task {Post-Script} -cmds {\n")
            self.file.write("        RemoteCmd {blender --background %s --python %s}\n" % ( spoolfull, bpy.context.scene.postscript ))
            self.file.write("    }\n")

        if bpy.context.scene.doclean:
            self.file.write("    Task {Cleaning Up} -cmds {\n")
            self.file.write("        RemoteCmd {sleep 5}\n")
            self.file.write("    }\n")
            
        self.file.write("}\n")
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
*********
* TODO! *
*********
- Figure out how to save the spooled file from the pre and post scripts.
- Add support for running custom pre/post-script on the file.
- Paths to python scripts need to be absolute to work.

*********
* LATER *
*********
- Consider if there is a need to run a script for each rendered frame.
- Add cleanup checkbox, for removing .alf and .blend file once the job is done.
- Add support for displaying progress per frame.
- Look at envkeys.
- Add custom icon of a tractor. :)
- Add Bake simulations (possibly try to split different sims on different nodes).
- Fix how it saves out spool files. Now it breaks relative texture paths in the file you have open.
-- Reported as bug #33108  ( http://projects.blender.org/tracker/index.php?func=detail&aid=33108&group_id=9&atid=498 ) - fix in repos

*********
* NOTES *
*********
PROCESS TREE
- Pre-Script for render/bake
- Bake all simulations before rendering
- Post-Bake Script
- Render frames
-- Render a frame
-- Render another frame
-- And another
- Post-Script for render
- Run cleanup

Job -title {test} -priority 2 -service {BlenderRender} -crews {dailies} -envkey {} -serialsubtasks 1 -subtasks {
    Task {Pre-Job Script} -cmds {
    	RemoteCmd {sleep 5}
    }    
    Task {Bake All Simulations} -cmds {
    	RemoteCmd {sleep 5}
    }    
    Task {Post-Bake Script} -cmds {
    	RemoteCmd {sleep 5}
    }    
    Task {Render Frames} -subtasks {
        Task {Render Frame 1} -cmds {
            RemoteCmd {sleep 5}
        }
        Task {Render Frame 2} -cmds {
            RemoteCmd {sleep 5}
        }
        Task {Render Frame 3} -cmds {
            RemoteCmd {sleep 5}
        }
    }
    Task {Post-Job Script} -cmds {
    	 RemoteCmd {sleep 5}
    }
    Task {Cleanup} -cmds {
    	 RemoteCmd {sleep 5}
    }
}
'''
