#!/usr/bin/env python
"""
Copyright (c) 2010 Sam Phippen <samphippen@googlemail.com> and Peter Law
<PeterJCLaw@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
from random import randint, seed
from pyglet import gl
from pyglet.graphics import OrderedGroup, Batch, Group
from pyglet import window, image
from time import sleep
from math import log
from BeautifulSoup import BeautifulStoneSoup

import argparse
import pyglet
import os,sys
import numpy as np
import ctypes

def clamp(x, lower, upper):
    if x > upper:
        x = upper
    elif x < lower:
        x = lower
    return x

class Triangle:

    def __init__(self):
        self.points = []
        self.color = [0,0,0,255]

    def clone(self):
        t = Triangle()
        t.points = self.points[0:]
        t.color = self.color[0:]
        return t

    def serialize_points(self):
        result = []
        for x,y in self.points:
            result.append(x)
            result.append(y)
        return result

    def serialize_color(self):
        return self.color[0:]

    def svg_soup_import(self, soup, height):
        """
        Import the triangle from a BeatufilSoup SVG polygon.
        """
        pts = soup['points'].split(' ')

        for i in range(0, len(pts)):
            x,y = pts[i].split(',')
            self.points.append([int(x), height - int(y)])

        sty = soup['style'].replace('; ', ';').split(';')

        for opt in sty:
            try:
                name,value = opt.split(':')
            except ValueError:
                continue

            if name == 'fill':
                self.color[0] = int(value[1:3], 16)
                self.color[1] = int(value[3:5], 16)
                self.color[2] = int(value[5:7], 16)

            elif name == 'fill-opacity':
                self.color[3] = int(255.0*float(value))

    def recolor_self_delta(self, delta):
        color = self.color
        x = randint(0,3)
        new_red,new_green,new_blue,new_alpha = color
        if x == 0:
            new_red = clamp(color[0]+randint(-delta,delta),0,255);
        elif x == 1:
            new_green = clamp(color[1]+randint(-delta,delta),0,255);
        elif x == 2:
            new_blue = clamp(color[2]+randint(-delta,delta),0,255);
        else:
            new_alpha = clamp(color[3]+randint(-delta,delta),0,255);
        self.color = [new_red, new_green, new_blue, new_alpha]

    def generate(self, xmax, ymax):
        self.points = [0]*3
        for i in xrange(0,3):
            x,y = randint(0,xmax),randint(0,ymax)
            self.points[i] = (x,y)
        self.color[0] = randint(0,255)
        self.color[1] = randint(0,255)
        self.color[2] = randint(0,255)
        self.color[3] = randint(0,255)

    def reshape_delta(self, xmax, ymax, delta):
        points = self.points
        for i in xrange(0, randint(0,4)):
            choice = randint(0,len(self.points)-1)
            x,y = randint(-delta,delta), randint(-delta, delta)
            x += points[choice][0]
            y += points[choice][1]
            x = clamp(x, 0, xmax)
            y = clamp(y, 0, ymax)
            points[choice] = (x,y)


class XTranslationGroup(Group):

    def __init__(self, x_translation, order):
        super(XTranslationGroup, self).__init__(parent=OrderedGroup(order))
        self._x_translation = x_translation

    def set_state(self):
        gl.glPushMatrix()
        gl.glTranslatef(self._x_translation,0,0)
        gl.glPushMatrix()
    def unset_state(self):
        gl.glPopMatrix()
        gl.glPopMatrix()

group = None

class Drawing:
    def __init__(self, width, height, fbo, background=[255,255,255]):
        self.width = width
        self.height = height
        self.triangles = []
        self.batch = Batch()
        self.bg_colour = background
        self.fb = fbo
        self.bg = self.batch.add( 6,
                        gl.GL_TRIANGLES,None,
                        ("v2i/static", (0,0,0,height,width,height,width,height,width,0,0,0)),
                        ("c3B/static",background*6)
                      )


    def clone(self):
        global group
        d = Drawing(self.width, self.height, self.fb, self.bg_colour)
        bufferlength = len(self.triangles)
        d.vertex_list = d.batch.add(
            bufferlength*3, gl.GL_TRIANGLES, group,
            ("v2i/stream", [0]*bufferlength*6),
            ("c4B/stream", [0]*bufferlength*12)
        )

        d.triangles = [t.clone() for t in self.triangles]
        d.refresh_batch()
        return d

    def mutate(self, num_mutations):
        triangles = self.triangles
        for i in xrange(0, num_mutations):
            e = randint(0,2)
            if e == 0:
                choice = randint(0, len(triangles)-1)
                triangles[choice].recolor_self_delta(5)
                self.update_index(choice)
            elif e == 1:
                choice = randint(0, len(triangles)-1)
                triangles[choice].reshape_delta(self.width, self.height, 25)
                self.update_index(choice)
            elif e == 2:
                c1 = randint(0, len(triangles)-1)
                c2 = clamp(c1 + randint(-5,5), 0, len(triangles)-1)
                triangles[c1],triangles[c2] = triangles[c2],triangles[c1]
                self.update_index(c1)
                self.update_index(c2)

    def update_index(self, i):
        vl = self.vertex_list
        t = self.triangles[i]
        i1 = i*6
        vl.vertices[i1:i1+6] = t.serialize_points()
        i1 *= 2
        vl.colors[i1:i1+12] = t.serialize_color()*3

    def draw(self):
        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, self.fb)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self.batch.draw()

    def refresh_batch(self):
        for i in xrange(0, len(self.triangles)):
            self.update_index(i)

    def generate(self, number_triangles):
        vertices = []
        colors = []
        for i in xrange(0, number_triangles):
            t = Triangle()
            t.generate(self.width, self.height)
            self.triangles.append(t)

            vertices.extend(t.serialize_points())
            colors.extend(t.serialize_color()*3)
        self.vertex_list = self.batch.add(
            number_triangles*3, gl.GL_TRIANGLES, None,
            ("v2i/stream", vertices),
            ("c4B/stream", colors)
        )

        self.refresh_batch()

    def svg_import(self, svg_file):
        """
        Import the drawing from an SVG file.
        """
        xml = open(svg_file).read()
        soup = BeautifulStoneSoup(xml).svg

        # Width and Height
        w = int(soup['width'].replace('px', ''))
        h = int(soup['height'].replace('px', ''))

        if w != self.width or h != self.height:
            raise Exception("Image dimensions don't match.")
        # two clockwise round triangles make a square
        self.bg.vertices = [ 0,0,
                             0,h,
                             w,h,
                             w,h,
                             w,0,
                             0,0]

        # Background colours
        try:
            name,value = soup.rect['style'].split(':')
        except ValueError:
            pass

        if name == 'fill':
            self.bg_colour[0] = int(value[1:3], 16)
            self.bg_colour[1] = int(value[3:5], 16)
            self.bg_colour[2] = int(value[5:7], 16)

        self.bg.colors = self.bg_colour*6

        # Polygons
        polygons = soup.findAll('polygon')

        vertices = []
        colors = []
        for p in polygons:
            T = Triangle()
            T.svg_soup_import(p, self.height)
            self.triangles.append(T)

            vertices.extend(T.serialize_points())
            colors.extend(T.serialize_color()*3)
        self.vertex_list = self.batch.add(
            len(polygons)*3, gl.GL_TRIANGLES, XTranslationGroup(self.width * 2, 1),
            ("v2i/stream", vertices),
            ("c4B/stream", colors)
        )

        self.refresh_batch()

    def svg_export(self, image_file, svg_file):
        """
        Export the drawing to an SVG file.
        """

        f = open(svg_file,"w")
        f.write('''<?xml version="1.0" standalone="no"?>
        <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
        "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">

        <svg width="%dpx" height="%dpx" viewport="0 0 %d %d" version="1.1"
        xmlns="http://www.w3.org/2000/svg">''' % (self.width,self.height,self.width,self.height))

        f.write('\n\t<rect width="100%%" height="100%%" style="fill:#%02x%02x%02x;" />' %
                ( self.bg_colour[0],self.bg_colour[1],self.bg_colour[2] )
            )
        for t in self.triangles:
            f.write('''\n\t<polygon points="%d,%d %d,%d %d,%d" style="fill:#%02x%02x%02x; fill-opacity:%f;" />''' % (
                t.points[0][0],
                self.height - t.points[0][1],
                t.points[1][0],
                self.height - t.points[1][1],
                t.points[2][0],
                self.height - t.points[2][1],
                t.color[0],t.color[1],t.color[2],t.color[3]/255.0
            ))

        f.write("\n</svg>")
        f.close()

image_pixels = None

def compute_diff(array):
    global keeps
    a = np.frombuffer(array, dtype=np.uint8)
    result = np.square(np.subtract(a, image_pixels))

    return np.sum(result, dtype=np.uint64)

def draw_parent(parent, width):
    gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, 0)
    parent.blit(width,0)

parent = None
parentdiff = None
keeps = []

newdrawing = None
olddrawing = None

def update(dt):
    global newdrawing
    global olddrawing

    #delete stale framebuffers
    fbref = None
    olddrawing = newdrawing.clone()
    newdrawing.mutate(5)

blitted = 0
image_pixels = None
i = 0

DEFAULT_NUM_POLYGONS = 250

def main(image_file, num_polygons=DEFAULT_NUM_POLYGONS, resume=False):
    global image_pixels
    global keeps
    global newdrawing, olddrawing
    global blitted

    pic = image.load(image_file)
    width = pic.width
    height = pic.height
    size = width*height

    #setup the framebuffer
    # create our frame buffer
    fbo = gl.GLuint()
    gl.glGenFramebuffersEXT(1, ctypes.byref(fbo))
    gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, fbo)

    # allocate a texture and add to the frame buffer
    tex = image.Texture.create_for_size(gl.GL_TEXTURE_2D, width, height, gl.GL_RGBA)
    gl.glBindTexture(gl.GL_TEXTURE_2D, tex.id)
    gl.glFramebufferTexture2DEXT(gl.GL_FRAMEBUFFER_EXT,
    gl.GL_COLOR_ATTACHMENT0_EXT, gl.GL_TEXTURE_2D, tex.id, 0)

    status = gl.glCheckFramebufferStatusEXT(gl.GL_FRAMEBUFFER_EXT)
    assert status == gl.GL_FRAMEBUFFER_COMPLETE_EXT

    newdrawing = Drawing(width,height,fbo)

    try:
        os.path.isfile(resume)
    except TypeError:
        svg_file = image_file + '.svg'
        if resume == True:
            newdrawing.svg_import(svg_file)
        else:
            newdrawing.generate(num_polygons)
    else:
        newdrawing.svg_import(resume)
        svg_file = resume

    w = window.Window(width*2,height,"cows", vsync = False)
    w.set_visible(True)
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    fps = pyglet.clock.Clock()

    #use this for pixel dumps
    a = (gl.GLubyte * (4*size))(0)

    @w.event
    def on_close():
        gl.glDeleteFramebuffersEXT(1, ctypes.byref(olddrawing.fb))
        olddrawing.svg_export(image_file, svg_file)

    @w.event
    def on_draw():
        #w.clear()
        global parent
        global parentdiff
        global olddrawing,newdrawing
        global blitted
        global image_pixels
        global keeps
        global i

        if not blitted:
            """
            At the start we've not seen the target before,
            so draw it and store the pixel data.
            """
            gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            pic.blit(0,0)
            blitted = 1
            image_pixels = (gl.GLubyte * (4*size))(0)
            gl.glReadPixels(0,
                            0,
                            newdrawing.width,
                            newdrawing.height,
                            gl.GL_RGBA,
                            gl.GL_UNSIGNED_BYTE,
                            image_pixels
                           )
            image_pixels = np.frombuffer(image_pixels, dtype=np.uint8).astype(np.int32)

        # Draw the new child
        newdrawing.draw()

        # Read the pixel data for the child and find out if its any good
        gl.glReadPixels(0,
                        0,
                        newdrawing.width,
                        newdrawing.height,
                        gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, a)
        diff = compute_diff(a)

        if parent == None or diff < parentdiff:
            # The new drawing is better.
            # Redraw the parent as this child.
            # Set this child's diff as the new one to beat.
            parent = image.ImageData(newdrawing.width,newdrawing.height,"RGBA",a)
            parentdiff = diff
            draw_parent(parent, newdrawing.width)
        else:
            # The new drawing sucks. Replace it
            newdrawing = olddrawing
        i += 1

        if (i % 20 == 0):
            # Use the window title to let the user know how we're doing
            w.set_caption("%s %s %s %s" % (
                fps.get_fps(),
                parentdiff,
                log(parentdiff,10),
                i,
            ))

        fps.tick()

    # Isolate and mutate the child on each clock tick
    pyglet.clock.schedule(update)
    # Set it running
    pyglet.app.run()


def parse_args():
    parser = argparse.ArgumentParser(
        description="A genetic hill-climber for reproducing images as SVGs",
    )
    parser.add_argument(
        'image_file',
        help="The image file to attempt to match.",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--polygons',
        action='store',
        type=int,
        default=DEFAULT_NUM_POLYGONS,
        help="The number of polygons to use (default: %(default)d). Using "
             "fewer polygons is faster. Using more polygons usually results in "
             "a closer match.",
    )

    group.add_argument(
        '--resume',
        nargs='?',
        metavar='SVG_FILE',
        action='store',
        default=False,
        help="Whether or not to resume from a previous session. When the "
             "graphics window is closed, the current state will be saved as an "
             "SVG file with the same base name as the original image. By "
             "default, resuming uses that saved SVG file, though other paths "
             "can also be specified (and will be saved back to).",
    )

    args = parser.parse_args()

    if args.resume is None:
        args.resume = True

    return args


if __name__ == "__main__":
    #import cProfile,pstats
    #prof = cProfile.Profile()
    #prof = prof.runctx("main()", globals(), locals())
    #stats = pstats.Stats(prof)
    #stats.sort_stats("cumulative")
    #stats.print_stats(800)
    #stats.print_callees()
    #stats.print_callers()

    args = parse_args()
    main(args.image_file, args.polygons, args.resume)
