# Tractor Dispatcher for Blender
Plug-in for Blender to dispatch render jobs to Pixar's Tractor render manager.

Tractor Dispatcher for Blender is a simple tool for dispatching Cycles renders to a farm managed by Pixar's Tractor render manager.

To use it you need a render farm running tractor-engine, Pixar Tractor licenses and the Tractor python API to be in the Pythonpath so blender can find it (i.e. import tractor.api.author as author)


# Installation

  1. Download the latest version of Tractor Dispatcher for Blender [here][1].
  2. Unpack the render\_tractor\_dispatcher.tar.gz, and copy render\_tractor\_dipatcher.py into (blender_folder)/2.93/scripts/addons/
  3. In Blender open File>User Preferences...>Addons and enter tractor in the search field. And activate the Render:Tractor Dispatcher addon by checking the checkbox next to it.

You should now have a Tractor Dispatcher pane at the bottom of the Properties>Render panel that looks something like this.

![Tractor Dispatcher interface](https://ragtag.net/xternal/github/tractor-dispatcher-for-blender/farmland.png)


# How to Use

Simply define a spool path (see below), assign a crew, and hit the Dispatch Job button. Tractor Dispatcher will save a copy of your .blend file to your spool path and start a render job on the farm.

# Options

Most of these are standard features of Tractor, so see [Pixar's Tractor documentation][3] for additional details.

**Priority**
Priority for the rendre job. Higher numbers will give your job higher priority in the rende queue.

**Crews**
Space separated list of crews to use for this job. If the environment variable DEPARTMENT is defined here, it will be used by default.

**Envkey**
Space separated environment variables to pass to Tractor. If you have PROJECTNAME, ASSET or DEPARTMENT dfined in your environment these will automatically be added to your envkeys.

**Service Key Expr**
Service Key Expression allows jobs to be matched with farm nodes that can run them. This defaults to Cycles. What farm nodes provide Cycles render can be defined in the blade.config for you Tractor Engine. See [Pixar's Tractor documentation][3] for details.

**Spool Path**
When you dispatch a job to Tractor, Blender will first save out a copy of your file to this path which it uses to render from. Make sure this path is on a shared network storage and is accessible by all the farm nodes.

**Use Full Binary Path**

This defines if the full path to Blender should be used instead of just 'blender'. This can be handy if you're using multiple versions of Blender, and want to be able to render from different ones, otherwise you can leave it unchecked.

# Using Caches

Note! I have yet to test if the below is still the case with v2.x.x of the Tractor Dispatcher. 

There are some issues with using the tractor dispatcher with particle, softbody and other caches, since the dispatchers saves out a copy of your file to a different location, the path to the cache may break. For a couple of tools you can choose to use external cache, and enter an absolute path to where you cache is saved, which will work with Tractor.

But, for instance, particle and soft body cache is a little more complicated. There is no way, as far as I know, to point to the cache on disk using an absolute path. In fact Blender simply looks in the same folder your .blend file is in for a blendcache folder with the name blendcache\_(your\_file\_name). The solution is to symbolically link (or copy) you blendcache folder in your spool directory alongside your spooled .blend file. The Tractor Dispatcher adds 6 numbers to end of the spooled file, to make each dispatched job unique, so these need to be included too. For instance, a spooled file of bob.blend called bob\_123456.blend, would need a folder (or link) called blendcache\_bob\_123456 with the cache in. Once that is done, Restart All Tasks for your job in the Tractor Dashboard.

To make sure your linked cache is working correctly, you can simply open the spooled file in Blender and see if it's behaving as expected.


# Release Notes

See [CHANGELOG.md][2]

 [1]: https://github.com/ragtag/tractor-dispatcher-for-blender/releases "Download  latest Tractor Dispatcher for Blender"
 [2]: https://github.com/ragtag/tractor-dispatcher-for-blender/blob/master/CHANGELOG.md
 [3]: https://rmanwiki.pixar.com/display/TRA/Tractor+2
