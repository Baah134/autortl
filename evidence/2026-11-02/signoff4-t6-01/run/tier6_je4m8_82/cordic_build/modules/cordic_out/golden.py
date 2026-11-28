def init():
    return dict()


def step(state, inputs):
    outputs = dict()

    x_value = int(inputs.get("x_in", 0)) & 0x3ffff
    if x_value & 0x20000:
        x_value -= 0x40000
    x_sum = (x_value + 2) & 0x7ffff

    y_value = int(inputs.get("y_in", 0)) & 0x3ffff
    if y_value & 0x20000:
        y_value -= 0x40000
    y_sum = (y_value + 2) & 0x7ffff

    outputs["cos_out"] = (x_sum >> 2) & 0xffff
    outputs["sin_out"] = (y_sum >> 2) & 0xffff
    return state, outputs