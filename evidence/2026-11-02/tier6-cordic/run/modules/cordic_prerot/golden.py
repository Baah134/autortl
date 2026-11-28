def init():
    return dict()

def step(state, inputs):
    angle = int(inputs.get("angle", 0)) & 0xFFFF
    quadrant = (angle >> 14) & 0x3

    if quadrant == 1 or quadrant == 2:
        x0 = (1 << 18) - 39797
        reduced = angle ^ 0x8000
    else:
        x0 = 39797
        reduced = angle

    z0 = (reduced << 4) & 0xFFFFF

    outputs = dict()
    outputs["x0"] = x0 & 0x3FFFF
    outputs["z0"] = z0
    return state, outputs