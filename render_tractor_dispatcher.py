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
Dispatch render jobs to Pixar's Tractor render farm manager.

See https://github.com/ragtag/tractor-dispatcher-for-blender for docs.

This script is only tested on Linux.
'''

bl_info = {
    "name": "Tractor Dispatcher",
    "author": "Ragnar Brynjulfsson",
    "version": (2, 0, 0),
    "blender": (2, 93, 0),
    "location": "Properties > Render > Tractor Dispatcher",
    "description": "Dispatch jobs to Pixar's Tractor render farm manager ",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Render"}


import os
import shlex
from time import gmtime, strftime
from tempfile import gettempdir

import bpy
from bpy.props import IntProperty, StringProperty, BoolProperty, FloatProperty

import tractor.api.author as author


bpy.types.Scene.priority = FloatProperty(
    name="Priority", 
    description="Priority in the Tractor job queue",
    min = 0.0, max = 1000000.0,
    default = 1.0
    )

if 'PROJECTNAME' in os.environ:
    projectname = os.getenv('PROJECTNAME')
else:
    projectname = ''
bpy.types.Scene.project = StringProperty(
    name="Project",
    description="Name of the project you're working on",
    maxlen=4096,
    default=projectname
    )

if 'DEPARTMENT' in os.environ:
    crew = os.getenv('DEPARTMENT')
else:
    crew = ''
bpy.types.Scene.crews = StringProperty(
    name="Crews",
    description="Space seperated list of crews to use",
    maxlen=4096,
    default=crew
    )

bpy.types.Scene.servicekey = StringProperty(
    name="Service Key Expr",
    description="Service Key Expr used by Tractor",
    maxlen=4096,
    default="Cycles"
)

envkeys = []
if 'PROJECTNAME' in os.environ:
    envkeys.append(
        "PROJECTNAME={name}".format(name=os.getenv('PROJECTNAME'))
    )
if 'ASSET' in os.environ:
    envkeys.append(
        "ASSET={asset}".format(asset=os.getenv('ASSET'))
    )
if 'DEPARTMENT' in os.environ:
    envkeys.append(
        "DEPARTMENT={department}".format(department=os.getenv('DEPARTMENT'))
    )

bpy.types.Scene.envkey = StringProperty(
    name="Envkey",
    description="EnvKey's separated by space (e.g. PROJECT=amazing SHOT=sh010)",
    maxlen=4096,
    default=" ".join(envkeys)
    )

bpy.types.Scene.spool = StringProperty(
    name="Spool Path",
    description="Farm readable path to where to save a copy of the  Blender file used for rendering",
    maxlen=4096,
    default=gettempdir(),
    subtype='DIR_PATH'
    )

bpy.types.Scene.usebinarypath = BoolProperty(
    name="Use Full Binary Path",
    description="Use the full path to the Blender executable",
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
        row.prop(sce, "project")
        row =layout.row()
        row.prop(sce, "priority")

        row = layout.row()
        row.prop(sce, "crews")

        row = layout.row()
        row.prop(sce, "envkey")
        row = layout.row()
        row.prop(sce, "servicekey")

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
        ''' Returns preformated time for now '''
        return strftime("%H%M%S", gmtime())

    def execute(self, context):
        ''' Dispatch the job to Tractor '''

        # Spool out the blender file.
        spooledfiles = []
        if not os.path.exists(bpy.context.scene.spool):
            os.makedirs(bpy.context.scene.spool)
        basefilename = os.path.basename(os.path.splitext(bpy.data.filepath)[0])
        blendshort = "%s_%s.blend" % (basefilename, self.now())
        blendfull = os.path.join(bpy.context.scene.spool, blendshort)
        bpy.ops.wm.save_as_mainfile(
            filepath=blendfull, 
            copy=True, 
            relative_remap=True
        )
        spooledfiles.append(blendfull)

        # Define path to blender
        blender_binary = "blender"
        if bpy.context.scene.usebinarypath:
            blender_binary = bpy.app.binary_path

        # Create a Tractor job
        self.job = author.Job(
            title="blender - {filename} - {collection}".format(
                filename=basefilename,
                collection="unknow"
            ),
            priority=bpy.context.scene.priority,
            service=bpy.context.scene.servicekey,
            projects=[bpy.context.scene.project],
            crews=shlex.split(bpy.context.scene.crews),
            envkey=shlex.split(bpy.context.scene.envkey)
        )

        # Render frames
        for f in range(
                bpy.context.scene.frame_start,
                bpy.context.scene.frame_end + 1,
                bpy.context.scene.frame_step):
            cmd = "{blender_binary} --background {blendfull} "\
                  "--frame-start {frame_start} --frame-end {frame_end} "\
                  "--frame-jump 1 --render-anim".format(
                      blender_binary=blender_binary,
                      blendfull=blendfull,
                      frame_start=f,
                      frame_end=f
                  )
            render_task = author.Task(
                title='Render frame {frame}'.format(frame=f),
                argv=shlex.split(cmd)
            )
            self.job.addChild(render_task)

        self.job.spool()
        return{'FINISHED'}    
        

def register():
    bpy.utils.register_class(OBJECT_OT_Button)
    bpy.utils.register_class(TractorDispatcherPanel)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_Button)
    bpy.utils.unregister_class(TractorDispatcherPanel)


if __name__ == "__main__":
    register()
