from random import randint

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
        

    def serialize_points(self):
        result = []
        for x,y in self.points:
            result.append(x)
            result.append(y)

    def serialize_color(self):
        return self.color[0:]

    def recolor_self_delta(self, delta):
        new_red = clamp(self.color[0]+randint(-delta,delta),0,255);
        new_green = clamp(self.color[1]+randint(-delta,delta),0,255);
        new_blue = clamp(self.color[2]+randint(-delta,delta),0,255);
        new_alpha = clamp(self.color[3]+randint(-delta,delta),0,255);
        self.has_changed = True
    
    def generate(self, xmax, ymax):
        self.points = [0]*3
        for i in range(0,3):
            x,y = randint(0,xmax),randint(0,ymax)
            self.points[i] = (x,y)
        self.color[0] = randint(0,255)
        self.color[1] = randint(0,255)
        self.color[2] = randint(0,255)
        self.color[3] = randint(0,255)
        self.has_changed = True

    def reshape_delta(self, xmax, ymax, delta):
        for i in range(0, randint(0,2)):
            choice = randint(0,len(self.points)-1)
            x,y = randint(-delta,delta)
            x += self.points[choice][0]
            y += self.points[choice][1]
            x = clamp(x, 0, xmax)
            y = clamp(y, 0, ymax)
            self.points[choice] = (x,y)
        self.has_changed = True

class Drawing:
    def __init__(self, width, height):
        self.width = width
        self.height = height
     
