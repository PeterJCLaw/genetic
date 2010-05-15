#!/usr/bin/env python
"""
Copyright (c) 2010 Sam Phippen <samphippen@googlemail.com>

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

import pyglet
import sys
import numpy as np
from math import log

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
        self.has_changed = False
    
    def clone(self):
        t = Triangle()
        t.points = self.points[0:]
        t.color = self.color[0:]
        t.has_changed = self.has_changed 
        return t

    def serialize_points(self):
        result = []
        for x,y in self.points:
            result.append(x)
            result.append(y)
        return result

    def serialize_color(self):
        return self.color[0:]

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
        self.has_changed = True
    
    def generate(self, xmax, ymax):
        self.points = [0]*3
        for i in xrange(0,3):
            x,y = randint(0,xmax),randint(0,ymax)
            self.points[i] = (x,y)
        self.color[0] = randint(0,255)
        self.color[1] = randint(0,255)
        self.color[2] = randint(0,255)
        self.color[3] = randint(0,255)
        self.has_changed = True

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
        self.has_changed = True


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
class Drawing:
    def __init__(self, width, height, batch):
        self.width = width
        self.height = height
        self.triangles = []
        self.batch = batch
        self.batch.add( 6, 
                        gl.GL_TRIANGLES,XTranslationGroup(2 * width, 0),
                        ("v2i/static", (0,0,0,height,width,height,width,height,width,0,0,0)),
                        ("c3B/static",[0,0,0]*6)
                      )

        
         
    def clone(self):
        d = Drawing(self.width, self.height, Batch())
        bufferlength = len(self.triangles)
        d.vertex_list = d.batch.add(
            bufferlength*3, gl.GL_TRIANGLES, XTranslationGroup(self.width * 2, 1),
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
        self.vertex_list.vertices[i*6:(i*6)+6] = self.triangles[i].serialize_points()
        self.vertex_list.colors[i*12:i*12+12] = self.triangles[i].serialize_color()*3               
    
    def draw(self):
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
            t.has_changed = False
            self.triangles.append(t)

            vertices.extend(t.serialize_points())
            colors.extend(t.serialize_color()*3)
        self.vertex_list = self.batch.add(
            number_triangles*3, gl.GL_TRIANGLES, XTranslationGroup(self.width * 2, 1), 
            ("v2i/stream", vertices),
            ("c4B/stream", colors)
        )

        self.refresh_batch()

image_pixels = None
def compute_diff(array):
    global keeps
    a = np.frombuffer(array, dtype=np.uint8).astype(np.int32)
    result = np.square(np.subtract(a, image_pixels))
    
    return np.sum(result, dtype=long)
def draw_parent(parent, width):
    parent.blit(width,0)

parent = None
parentdiff = None
keeps = []

newdrawing = None
olddrawing = None

def update(dt):
    global newdrawing
    global olddrawing
    if(isinstance(newdrawing, Drawing) == False):
        newdrawing = Drawing(100,100,Batch())
        newdrawing.generate(1)
    olddrawing = newdrawing.clone()
    newdrawing.mutate(5)
    
blitted = 0
image_pixels = None
i = 0
def main():
    global image_pixels
    global keeps
    global newdrawing, olddrawing
    global blitted
    pic = image.load(sys.argv[1])
    width = pic.width
    height = pic.height
    size = width*height
    #setup the drawing with 100 triangles
    b = Batch()
    newdrawing = Drawing(width,height, b)
    newdrawing.generate(6)
    w = window.Window(width*3,height,"cows", vsync = False)
    w.set_visible(True)
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    fps = pyglet.clock.Clock()
    
    #use this for pixel dumps
    a = (gl.GLubyte * (4*size))(0)
    print len(a)
    @w.event
    def on_close():
        width,height = olddrawing.width,olddrawing.height
        f = open(sys.argv[1] + ".svg","w")
        f.write('''<?xml version="1.0" standalone="no"?>
        <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
        "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">

        <svg width="%dpx" height="%dpx" viewport="0 0 %d %d" version="1.1"
        xmlns="http://www.w3.org/2000/svg">''' % (width,height,width,height))
        f.write('''<rect width="100%" height="100%" style="fill:#000000;"/>''')
        for triangle in olddrawing.triangles:
            f.write('''<polygon points="%d,%d %d,%d, %d,%d" style="fill:#%02x%02x%02x; fill-opacity:%f;"/>''' % (
                triangle.points[0][0],
                height-triangle.points[0][1],
                triangle.points[1][0],
                height-triangle.points[1][1],
                triangle.points[2][0],
                height-triangle.points[2][1],
                triangle.color[0],triangle.color[1],triangle.color[2],triangle.color[3]/255.0

            ))
        f.write("</svg>")
        f.flush()
        f.close()

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
        if(isinstance(newdrawing, Drawing) == False):
            newdrawing = Drawing(100,100,Batch())
            newdrawing.generate(400)
        newdrawing.draw()
        gl.glReadPixels(newdrawing.width*2, 
                        0, 
                        newdrawing.width,
                        newdrawing.height,
                        gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, a)
        diff = compute_diff(a)
        
        if parent == None or diff < parentdiff:
            parent = image.ImageData(newdrawing.width,newdrawing.height,"RGBA",a)
            parentdiff = diff
            draw_parent(parent, newdrawing.width)
        else:
            newdrawing = olddrawing
        i += 1
        if (i % 20 == 0):
            w.set_caption(str(fps.get_fps())+" "+str(parentdiff) + " "+str(log(parentdiff,10)))
        #pic.blit(0,0)
        if not blitted:
            pic.blit(0,0)
            blitted = 1

        fps.tick()

    pyglet.clock.schedule(update)
    pyglet.app.run()

    
if __name__ == "__main__":
    main()
