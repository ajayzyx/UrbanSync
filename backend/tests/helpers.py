from shapely.geometry import box


def sq(x0, y0, w=15, h=28):
    return box(x0, y0, x0 + w, y0 + h)
