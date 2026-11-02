def init():
    return dict(F=65535)

def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        state["F"] = 65535
        outputs["out_crc"] = 0
        outputs["out_last"] = 0
        return state, outputs

    value = (state.get("F", 65535) ^ ((int(inputs.get("in_data", 0)) & 255) << 8)) & 65535
    for bit in range(8):
        if value & 32768:
            value = ((value << 1) ^ 4129) & 65535
        else:
            value = (value << 1) & 65535

    last = int(bool(inputs.get("in_last", 0)))
    outputs["out_crc"] = value
    outputs["out_last"] = last
    if last:
        state["F"] = 65535
    else:
        state["F"] = value
    return state, outputs