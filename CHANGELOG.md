
0.12-alpha10 (2017-09-04)
==========
 * Improved user prompts
 * Inf/NaN guard for flowmodules
 * Realtime world support
 * Reliable code reloading


0.11-alpha9 (2017-06-26)
==========
 * Add adhoc-monitors for plotting simple scalar values
 * Node states now support numpy data structrues
 * Add autosave-functionality for nodenets
 * Change the stepping order from `nodenet, world, sleep` to `nodenet, sleep, world`


0.10-alpha8 (2017-06-06)
==========
 * use matplotlib's webagg for plotting


0.9-alpha7 (2017-02-13)
==========
 * New structure for native module / recipe discovery
 * Live reloading of World and worldadapter code
 * Outsourced world and worldadapter definitions
 * Flowmodules for theano_engine
 * Recorders for theano_engine
 * High-dimensional native modules for theano_engine
 * Configurable Worldadapters


0.8-alpha6 (2016-04-22)
==========

 * Operations for selections of nodes/nodespaces
 * Test infrastructure for nodenets and native modules
 * Gradient descent native modules built-in
 * Nodenet/native module data structure changed
 * Faster sensors for theano
 * Configurable worlds
 * New timeseries world
 * Netapi console if serving for localhost only


0.7-alpha5 (2016-02-04)
==========

 * Changed the nodenet data protocol to only transfer diffs while stepping
 * Windows compatibility & instructions


0.6-alpha4 (2015-11-17)
==========

 * Made the theano engine the non-experimental default
 * Made partitions configurable
 * Introduced LSTMs
 * Introduced Visualization API
 * Introduced dashboard


0.5-alpha3 (2015-07-16)
==========

 * Improved monitor and logging UI
 * Introduced runner conditions
 * Introduced netapi fragment generation
 * Introduced concept of "Partitions"


0.4-alpha2 (2015-06-05)
==========

 * Introduced Comment nodes
 * Introduced global modulators and Doernerian emotional model
 * Introduced por/ret link decay
 * Introduced recipes: python scripts that can be run from the nodenet editor  and have netapi access
 * Copy & paste functionality in nodenet editor
 * Snap to grid in nodenet editor
 * Nodenet editor setting for rendering links: always, for currently selected nodes, or never
 * Nodenet editor can link multiple selected nodes at once
 * Improved nodenet editor user experience when zoomed out
 * Additional monitor types, including link weight monitors
 * Display origin-gate & target-slot in link-sidebar

 * Introduced theano_engine, an engine for running nodenets on top of numpy/theano (requires additional configuration)
 * Introduced Minecraft connectivity (requires additional configuration)


0.3-alpha1 (2014-06-30)
==========

First alpha release
