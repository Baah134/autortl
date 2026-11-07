def init():
    return dict(frame=65535)

def step(state, inputs):
    outputs = dict()
    rst = int(inputs.get("rst", 0)) & 1

    if rst:
        state["frame"] = 65535
        outputs["out_crc"] = 0
        outputs["out_last"] = 0
    else:
        data = int(inputs.get("in_data", 0)) & 255
        last = int(inputs.get("in_last", 0)) & 1
        crc = (int(state.get("frame", 65535)) & 65535) ^ (data << 8)

        for index in range(8):
            if crc & 32768:
                crc = ((crc << 1) ^ 4129) & 65535
            else:
                crc = (crc << 1) & 65535

        outputs["out_crc"] = crc
        outputs["out_last"] = last
        if last:
            state["frame"] = 65535
        else:
            state["frame"] = crc

    return state, outputs