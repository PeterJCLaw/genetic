#!/usr/bin/env python

from BeautifulSoup import BeautifulStoneSoup

from genetic import Triangle, Drawing

def svg_import(file):
    xml = open(file).read()
    soup = BeautifulStoneSoup(xml).svg

    w = int(soup['width'].replace('px', ''))
    h = int(soup['height'].replace('px', ''))

    polygons = soup.findAll('polygon')
    num_polygons = len(polygons)

    D = Drawing(w, h)

    for p in polygons:
        pts = p['points'].split(' ')

        T = Triangle()

        for i in range(0, len(pts)):
            x,y = pts[i].split(',')
            T.points.append([int(x), h-int(y)])

        sty = p['style'].replace('; ', ';').split(';')

        for opt in sty:
            try:
                name,value = opt.split(':')
            except ValueError:
                continue

            if name == 'fill':
                T.color[0] = int(value[1:2], 16)
                T.color[1] = int(value[3:4], 16)
                T.color[2] = int(value[5:6], 16)

            elif name == 'fill-opacity':
                T.color[3] = int(255.0*float(value))

        D.triangles.append(T)

    return D.clone()


if __name__ == '__main__':
    import sys
    svg_import(sys.argv[1])
