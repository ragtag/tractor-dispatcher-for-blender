# Tractor Dispatcher for Blender
Plug-in for Blender to dispatch render jobs to Pixar's Tractor render manager

Tractor Dispatcher for Blender is a simple tool for dispatching jobs to a render farm managed by Pixar's Tractor render manager. It can be used both for rendering, and for running arbitrary batch jobs defined by a Python scripts.

To use it you need a render farm running tractor-engine, Pixar Tractor licenses and tractor-spooly.py in path when you start blender.

**IMPORTANT NOTE!**

If running Blender 2.64 and Cycles, this tool will break the paths to your textures, due to a <a title="Bug #33108" href="http://projects.blender.org/tracker/index.php?func=detail&aid=33108&group_id=9&atid=498" target="_blank" rel="noopener">bug</a> in Blender that has since been fixed. Either use Blender 2.65, or make sure you save your file BEFORE dispatching a render job, and reload it after you dispatch it. Note that the file saved in the spool folder will still be intact, so you can grab that if the script corrupts your file.

# Installation

  1. Download the latest version of Tractor Dispatcher for Blender [here][1].
  2. Unpack the render\_tractor\_dispatcher.tar.gz, and copy render\_tractor\_dipatcher.py into (blender_folder)/2.65/scripts/addons/
  3. In Blender open File>User Preferences...>Addons and enter tractor in the search field. And activate the Render:Tractor Dispatcher addon by checking the checkbox next to it.

You should now have a Tractor Dispatcher pane at the bottom of the Properties>Render panel that looks something like this.

<p style="text-align: center;">
  <a href="https://ragnarb.com/blog/wp-content/uploads/2012/12/tractor-dispatcher-for-blender-panel.png"><img loading="lazy" class="size-full wp-image-67 aligncenter" title="tractor-dispatcher-for-blender-panel" src="https://ragnarb.com/blog/wp-content/uploads/2012/12/tractor-dispatcher-for-blender-panel.png" alt="" width="318" height="257" srcset="https://ragnarb.com/blog/wp-content/uploads/2012/12/tractor-dispatcher-for-blender-panel.png 318w, https://ragnarb.com/blog/wp-content/uploads/2012/12/tractor-dispatcher-for-blender-panel-300x242.png 300w" sizes="(max-width: 318px) 100vw, 318px" /></a>
</p>

# How to Use

Simply define a spool path (see below), assign a crew, and hit the Dispatch Job button. Tractor Dispatcher will create an .alf job script, save a copy of your .blend file and pre/post-scripts if you have any, and run tractor-spool.py

# Options

**Render Scene**

Tells Tractor that it should render the scene. You would un-check this if you only wanted to run a python script on the scene, and not render this. This way you can for instance use the Tractor Dispatcher to dispatch fluid simulations to your farm (though it will unfortunately only run on one render node).

**Show Progress**

This shows progress bars in Tractor for each frame. This uses some basic *nix tools, so if running this on Windows you want to un-check this box (note that this script has only been tested on Linux). If you're using Blender's internal renderer the progress bar will run from 0 to full for each motion blur pass, like the progress bar does in Blenders interface.

**Priority, Crews and Envkey**

These are all standard features of Tractor. See Pixar's Tractor documentation for details.

**Pre/Post-Script**

Pre-Script is a python script file that is run before a single frame is rendered, and Post-Script is a python script file that is run after a all frames have finished rendering. If you want to run a script before or after rendering each frame, look into bpy.app.handlers.render_post/pre in the Blender documentation.

**Spool Path**

This is the path where the .alf job script that Tractor uses to know which frames to render is placed. It is also where a copy of your .blend file and your pre/post-scripts is saved, and where Tractor reads them from. This means that all your render nodes must have access to this path, as well as any other textures and files your .blend file needs to render.

**Use Full Binary Path**

This defines if the full path to Blender should be written in the .alf job script. This can be handy if you're using multiple versions of Blender, and want to be able to render from different ones, otherwise you can leave it unchecked.

# Using Caches

There are some issues with using the tractor dispatcher with particle, softbody and other caches, since the dispatchers saves out a copy of your file to a different location, the path to the cache may break. For a couple of tools you can choose to use external cache, and  enter an absolute path to where you cache is saved, which will work with Tractor.

But, for instance, particle and soft body cache is a little more complicated. There is no way, as far as I know, to point to the cache on disk using an absolute path. In fact Blender simply looks in the same folder your .blend file is in for a blendcache folder with the name  blendcache\_(your\_file\_name). The solution is to symbolically link (or copy) you blendcache folder in your spool directory alongside your spooled .blend file. The Tractor Dispatcher adds 6 numbers to end of the spooled file, to make each dispatched job unique, so these need to be included too. For instance, a spooled file of bob.blend called bob\_123456.blend, would need a folder (or link) called blendcache\_bob\_123456 with the cache in. Once that is done, Restart All Tasks for your job in the Tractor Dashboard.

To make sure your linked cache is working correctly, you can simply open the spooled file in Blender and see if it's behaving as expected.

# Release Notes

1.0.0 - First public release for Blender 2.6x and 2.7x and Tractor 1.x

1.1.0 - Updated to work with Bledner 2.8x and Tractor 2.x

 [1]: https://github.com/ragtag/tractor-dispatcher-for-blender/releases "Download  latest Tractor Dispatcher for Blender"
