# Genetic Hill Climbing Image Matcher

Genetic is a Python 2 implementation of a genetic hill climber for image matching.
It was inspired in part by the JavaScript implementation at http://alteredqualia.com/visualization/evolve/.

## Dependencies
 * BeautifulSoup
 * numpy
 * pyglet

## Basic usage

Genetic expects to be passed a single image file to match:

``` shell
python genetic.py IMAGE_FILE
```

When running it will display a window which contains the target image, along
with the current attempt at matching that image (starting from a random seed).

Closing the window causes the current attempt to be saved as an SVG file
alongside the target image (with an additional `.svg` extension).

Matching can be continued from an existing SVG using the `--resume` argument.
Alternatively the starting number of polygons can be changed with `--polygons`.
See the `--help` for more details.

## Operation

Genetic iterates through a large number of possible images in search of one that
most closely matches the target. Each candidate image is comprised of a number
of polygons (currently triangles) of various colours and dimensions.

On each iteration, a number of mutations are applied to the current best
candidate image in order to produce a new candidate. The mutations are one of:
- reshaping a triangle (i.e: moving some of the corners)
- recolouring a triangle
- changing the order of a pair of triangles (so that one is now above the other)

The relative difference, in terms of pixels, between the target image and the
new candidate are then compared. If this is better than the current best
candidate then the new candidate is used as the current best.
