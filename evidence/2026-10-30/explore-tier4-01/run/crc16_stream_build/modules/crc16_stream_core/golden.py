def init():
    return dict(frame=65535)

def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        state["frame"] = 65535
        outputs["out_crc"] = 0
        outputs["out_last"] = 0
        return state, outputs

    crc = state.get("frame", 65535) ^ ((inputs.get("in_data", 0) & 255) << 8)
    count = 0
    while count < 8:
        if crc & 32768:
            crc = ((crc << 1) ^ 4129) & 65535
        else:
            crc = (crc << 1) & 65535
        count = count + 1

    last = inputs.get("in_last", 0) & 1
    outputs["out_crc"] = crc
    outputs["out_last"] = last
    if last:
        state["frame"] = 65535
    else:
        state["frame"] = crc
    return state, outputs