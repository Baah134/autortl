def init():
    return dict(frame=65535)

def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        state["frame"] = 65535
        outputs["out_crc"] = 0
        outputs["out_last"] = 0
        return state, outputs

    value = state.get("frame", 65535) ^ ((inputs.get("in_data", 0) & 255) << 8)
    for index in range(8):
        if value & 32768:
            value = ((value << 1) ^ 4129) & 65535
        else:
            value = (value << 1) & 65535

    outputs["out_crc"] = value
    outputs["out_last"] = inputs.get("in_last", 0) & 1
    if outputs["out_last"]:
        state["frame"] = 65535
    else:
        state["frame"] = value
    return state, outputs