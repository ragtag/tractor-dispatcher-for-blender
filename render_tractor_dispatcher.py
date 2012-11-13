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

WARNING!
This script is only tested on Linux, but should work on OSX too. It likely won't work on Windows, though you never know.
Prior to version 2.65 of Blender, this plug-in will break Cycles texture paths in your scene. This means that after you dispatch your scene to the farm, you need to reload it. This is due to bug #33108  ( http://projects.blender.org/tracker/index.php?func=detail&aid=33108&group_id=9&atid=498 ).

HOW TO USE
You will need a tractor-spool.py in path, Tractor licenses and a renderfarm to use this script. All file and texture paths, including the spool path need to be accessible from all the render nodes.

The Tractor Dispatcher will use the render setttings you've defined in your scene. There are a few additional settings you need to set in Tractor Dispatcher before you submit your job to the farm. 

Spool Path
You need to define the Spool Path. This is where the Tractor Dispatcher will save a copy of your .blend file for rendering, as well as save the .alf job script, and copies of your pre- and post-scripts if you're using them. The spool path needs to be available to all render nodes for reading (and writing if you're modifying the file with a pre-script before rendering).

Render Scene
The Render Scene checkbox tells the dispatcher if to actually render out any frames. You can uncheck this if you want to use the dispatcher simply to run a script on your file on a farm node.

Show Progress
Show Progress displays progress for each frame when rendering. This only works with Cycles and Blender's Internal renderer. If you're using another renderer you should disable this option. If you're rendering on Windows (something I've not tested), you should disable this option, as it uses a number of shell commands to extract the progress from the Blender output that are not available on Windows. Note that if you're using Blender Internal renderer and motion blur, the progress bar will go from zero to full for each pass of the motion blur, like the progress bar in Blender's GUI.

Crews and Envkey
Crews and Envkey are the crew you render as, and an arbitrary key you pass to the farm. You can read about them in Pixar's Tractor documentation.

Pre- and Post-Scripts
Pre-script is an optional python script that is run on the spooled .blend file before the rendering starts. These won't affect the scene you have open, only the temporary .blend file saved out for rendering. If you make changes to the .blend file in your script, remember to add bpy.ops.wm.save_mainfile(filepath=bpy.data.filepath) to the end of your script, to save out your changes before rendering starts.

Post-script is the same as the pre-script, but is run after all frames have finished rendering. It could for instance be used to notify you by mail that your render is done, or to do some processing on the newly rendered frames.

If you want to run scripts before or after rendering each frame, look into bpy.app.handlers.render_post/pre'''

bl_info = {
    "name": "Tractor Dispatcher",
    "author": "Ragnar Brynjulfsson",
    "version": (0, 8, 0),
    "blender": (2, 6, 4),
    "location": "Properties > Render > Tractor Dispatcher",
    "description": "Dispatch jobs to Pixar's Tractor render farm manager ",
    "warning": "Prior to version Blender 2.6.5, the dispatcher breaks texture paths in your scene",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Render"}

import bpy
from bpy.props import IntProperty, StringProperty, BoolProperty, FloatProperty

import os
import subprocess
from time import gmtime, strftime, sleep
from tempfile import gettempdir
from shutil import copy2


bpy.types.Scene.dorender = BoolProperty(
    name="Render Scene",
    description="Render the scene using current render settings",
    default=True
    )

bpy.types.Scene.showprogress = BoolProperty(
    name="Show Progress",
    description="Show per frame progress (only works on Linux or OSX with Cycles or Blender Internal renderer)",
    default=True
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

bpy.types.Scene.envkey = StringProperty(
    name="Envkey",
    description="Arbitrary key passed to the remote machine, used by AlfEnvConfig",
    maxlen=4096,
    default=""
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

bpy.types.Scene.spool = StringProperty(
    name="Spool Path",
    description="Path to where temporary files are stored (.alf script and .blend file)",
    maxlen=4096,
    default=gettempdir(),
    subtype='DIR_PATH'
    )

bpy.types.Scene.usebinarypath = BoolProperty(
    name="Use Full Binary Path",
    description="Use the full path to the Blender executable (check when using multiple versions of Blender)",
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
        row.prop(sce, "showprogress")

        row =layout.row()
        row.prop(sce, "priority")

        row = layout.row()
        row.prop(sce, "crews")
        row = layout.row()
        row.prop(sce, "envkey")

        row = layout.row()
        row.prop(sce, "prescript")
        row = layout.row()
        row.prop(sce, "postscript")

        row = layout.row()
        row.prop(sce, "spool")

        row = layout.row()
        row.prop(sce, "usebinarypath")

        row = layout.row()
        row.operator("object.button", text="Dispatch Job")


class OBJECT_OT_Button(bpy.types.Operator):
    bl_idname = "object.button"
    bl_label = "Button"
    bl_description = "Dispatch scene to tractor blades"
    mode = IntProperty(name="mode", default=1) 

    def now(self):
        # Returns preformated time for now.
        return strftime("%H%M%S", gmtime())

    def execute(self, context):
        # Dispatch the job to tractor.
        # Spool out the blender file.
        spooledfiles = []
        if not os.path.exists(bpy.context.scene.spool):
            os.makedirs(bpy.context.scene.spool)
        basefilename = os.path.basename(os.path.splitext(bpy.data.filepath)[0])
        blendshort = "%s_%s.blend" % (basefilename, self.now())
        blendfull = os.path.join(bpy.context.scene.spool, blendshort)
        bpy.ops.wm.save_as_mainfile(filepath=blendfull, copy=True, relative_remap=True)
        spooledfiles.append(blendfull)
        # Create the .alf script.
        blender_binary = "blender"
        if bpy.context.scene.usebinarypath:
            blender_binary = bpy.app.binary_path
        jobshort = "%s_%s.alf" % (basefilename, self.now())
        jobfull = os.path.join(bpy.context.scene.spool, jobshort)
        self.file = open(jobfull, 'w')
        spooledfiles.append(jobfull)
        self.file.write("Job -title {%s} -priority %s -service {BlenderRender} -crews {%s} -envkey {%s} -serialsubtasks 1 -subtasks {\n" % ( blendshort, bpy.context.scene.priority, bpy.context.scene.crews, bpy.context.scene.envkey ))

        # Run pre-script
        if bpy.context.scene.prescript:
            prefull = os.path.join(bpy.context.scene.spool, "%s_%s_pre.py" % ( basefilename, self.now() ))
            copy2(bpy.path.abspath(bpy.context.scene.prescript), prefull )
            self.file.write("    Task {Pre-Job Script} -cmds {\n")
            self.file.write("        RemoteCmd {%s --background %s --python %s}\n" % ( blender_binary, blendfull, prefull ))
            self.file.write("    }\n")
            spooledfiles.append(prefull)

        # Render frames
        bashwrap=""
        progresscmd=" "
        if bpy.context.scene.showprogress:
            if bpy.context.scene.render.engine == 'CYCLES':
                bashwrap="/bin/bash -c {"
                progresscmd=" | while read line;do echo \$line;echo \$line | grep 'Path Tracing Tile' | awk {'print \$(NF)'} | sed 's/$/*100/' | bc -l | cut -d. -f1| sed 's/^/TR_PROGRESS /;s/\$/%/';done}"
            if bpy.context.scene.render.engine == 'BLENDER_RENDER':
                bashwrap="/bin/bash -c {"
                progresscmd=" | while read line;do echo \$line;echo \$line | grep 'Scene, Part' | awk {'print \$(NF)'} | sed 's/-/\\\//g' | sed 's/$/*100/' | bc -l | cut -d. -f1| sed 's/^/TR_PROGRESS /;s/\$/%/';done}"
        if bpy.context.scene.dorender:
            self.file.write("    Task {Render Frames} -subtasks {\n")
            start = bpy.context.scene.frame_start
            end = bpy.context.scene.frame_end + 1
            step = bpy.context.scene.frame_step
            for f in range(start,end,step):
                self.file.write("        Task {Frame %s} -cmds {\n" % ( f ))
                self.file.write("            RemoteCmd {%s%s --background %s --frame-start %s --frame-end %s --frame-jump 1 --render-anim %s} -tags {intensive blender}\n" % ( bashwrap, blender_binary, blendfull, f, f, progresscmd ))
                self.file.write("        }\n")
            self.file.write("    }\n")

        # Run post-script
        if bpy.context.scene.postscript:
            postfull = os.path.join(bpy.context.scene.spool, "%s_%s_post.py" % ( basefilename, self.now() ))
            copy2(bpy.path.abspath(bpy.context.scene.postscript), postfull )
            self.file.write("    Task {Post-Script} -cmds {\n")
            self.file.write("        RemoteCmd {%s --background %s --python %s}\n" % ( blender_binary, blendfull, bpy.context.scene.postscript ))
            self.file.write("    }\n")
            spooledfiles.append(postfull)
            
        self.file.write("}\n")
        self.file.close()

        # Just to make doubly sure the .alf script is available on disk.
        sleep(1)
        # Dispatch the job to tractor.
        command = "tractor-spool.py %s" % (jobfull)
        if subprocess.call([ command, jobfull ], shell=True) != 0:
            raise RuntimeError("Failed to run tractor-spool.py, check that it's in path. The spooled files were still written out to %s" % ( bpy.context.scene.spool ))
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
********
* NEXT *
********
- Write documentation and set up web page for the script.
- Test if sleep is needed.
- Test on the farm.

*********
* TODO! *
*********
- Publish a beta version of the script after 2.65

************
* Versions *
************
0.8 - Alpha. Test and bug fix.
0.9 - Public beta. Bug fixing.
1.0 - Official release.
2.0 - Implement better error handling...maybe.
2.0 - Combine Blur pass with progress to get a non-repeating progressbar when rendering with Blender Internal render and motion blur.
3.0 - Bake simluations.
3.0 -- Find all available simulations in the scene, and make each selectable as needed.
3.0 -- Figure out a clever way to dispatch each sim to a different node, and then combine the cache in a new file for rendering.

*********
* NOTES *
*********
- Pre- and post frame scripts can simply use, bpy.app.handlers.render_post/pre in the file.
- Saving your spooled files in your pre script.
-- bpy.ops.wm.save_mainfile(filepath=bpy.data.filepath)

***************
* LIMITATIONS *
***************
- Not tested on Windows and OSX. While I've tried making everything as os independent as possible, I don't have access to a farm running on Windows or OSX. OSX will likely work, but for Windows you'll have to disable the progress display.
- The progress bar for each frame works incorrectly when using motion blur in the internal render. It will go from zero to full for each pass, rather than for the whole frame. This is a limitation of how Blender represents the progress, and Blender does the same in the internal GUI. Until that changes, this limitation will remain.
- Wait with publish until Blender 2.65, when the bug below has been fixed.
-- Reported as bug #33108  ( http://projects.blender.org/tracker/index.php?func=detail&aid=33108&group_id=9&atid=498 ) - fix in repos
'''
