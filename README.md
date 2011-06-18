Genetic is a Python implementation of a genetic hill climber for image matching.
It was inspired in part by the JavaScript implementation at http://alteredqualia.com/visualization/evolve/.

### Dependencies
 * BeautifulSoup
 * numpy
 * pyglet

### Operation
See the in-built help for how to run the script.

Genetic iterates through a large number of possible images in search of
one that most closely matches the target.
Since this can take a while it's recognised that you might want to do this
across several sessions.
Happily genetic can do this by saving to (& restoring from) svg files
saved with the same base name as the target image.
These svg files are created when the main window is closed.
When resuming this pattern can be used to automatically find the created
svg file, or an alternative can be specified.
