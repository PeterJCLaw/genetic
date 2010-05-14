from random import randint, seed
from pyglet import gl
from pyglet.graphics import OrderedGroup, Batch, Group
from pyglet import window
from time import sleep

import pyglet

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
        new_red = clamp(self.color[0]+randint(-delta,delta),0,255);
        new_green = clamp(self.color[1]+randint(-delta,delta),0,255);
        new_blue = clamp(self.color[2]+randint(-delta,delta),0,255);
        new_alpha = clamp(self.color[3]+randint(-delta,delta),0,255);
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
        for i in xrange(0, randint(0,4)):
            choice = randint(0,len(self.points)-1)
            x,y = randint(-delta,delta), randint(-delta, delta)
            x += self.points[choice][0]
            y += self.points[choice][1]
            x = clamp(x, 0, xmax)
            y = clamp(y, 0, ymax)
            self.points[choice] = (x,y)
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
        assert len(d.triangles) == len(self.triangles)
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
        vertices = []
        color = []
        vertex_list = self.vertex_list
         
        self.batch.draw()

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
        print len(colors), len(self.triangles)*3*4
        self.vertex_list = self.batch.add(
            number_triangles*3, gl.GL_TRIANGLES, XTranslationGroup(self.width * 2, 1), 
            ("v2i/stream", vertices),
            ("c4B/stream", colors)
        )

        for i in xrange(0, number_triangles):
            self.vertex_list.vertices[i*6:(i*6)+6] = self.triangles[i].serialize_points()
            self.vertex_list.colors[i*12:(i*12)+12] = self.triangles[i].serialize_color()*3


def main():
    width = 400
    height = 400
    b = Batch()
    d = Drawing(width,height, b)
    d.generate(100)
    w = window.Window(width*3,height,"cows", vsync = False)
    w.set_visible(True)
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
    fps = pyglet.clock.Clock()
    a = (gl.GLuint * (3*d.width*d.height))(0)
    @w.event
    def on_draw():
        #w.clear()
        d.draw()
        gl.glReadPixels(d.width*2, 0, d.width, d.height, gl.GL_RGB, gl.GL_UNSIGNED_INT, a)
        w.set_caption(str(fps.get_fps()))
        fps.tick()
    pyglet.clock.schedule(lambda x:d.mutate(3))
    pyglet.app.run()
if __name__ == "__main__":
    seed(3)
    main()
