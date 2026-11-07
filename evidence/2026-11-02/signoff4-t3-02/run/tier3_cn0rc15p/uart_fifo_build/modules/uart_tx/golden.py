def init():
    return dict(phase=0, count=0, data=0, bit=0, p=16)


def step(state, inputs):
    phase = state.get("phase", 0)
    count = state.get("count", 0)
    data = state.get("data", 0)
    bit_index = state.get("bit", 0)
    p = state.get("p", 16)

    if inputs.get("rst", 0):
        phase = 0
        count = 0
        data = 0
        bit_index = 0
    elif phase == 0:
        if inputs.get("tx_valid", 0):
            phase = 1
            count = p
            data = int(inputs.get("tx_data", 0)) & 255
            bit_index = 0
    elif phase == 1:
        if count > 1:
            count = count - 1
        else:
            phase = 2
            count = p
            bit_index = 0
    elif phase == 2:
        if count > 1:
            count = count - 1
        elif bit_index < 7:
            bit_index = bit_index + 1
            count = p
        else:
            phase = 3
            count = p
    elif phase == 3:
        if count == 1:
            if inputs.get("tx_valid", 0):
                phase = 1
                count = p
                data = int(inputs.get("tx_data", 0)) & 255
                bit_index = 0
            else:
                phase = 0
                count = 0
        else:
            count = count - 1

    state["phase"] = phase
    state["count"] = count
    state["data"] = data
    state["bit"] = bit_index
    state["p"] = p

    if phase == 0:
        tx = 1
        tx_ready = 1
    elif phase == 1:
        tx = 0
        tx_ready = 0
    elif phase == 2:
        tx = (data >> bit_index) & 1
        tx_ready = 0
    else:
        tx = 1
        tx_ready = int(count == 1)

    outputs = dict(tx_ready=tx_ready, tx=tx)
    return state, outputs