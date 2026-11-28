def init():
    return dict(sync1=1, sync2=1, mode=0, offset=0, vote7=0, vote8=0, vote9=0, received=0, rx_data=0, OVERSAMPLE_DIV=2)

def step(state, inputs):
    outputs = dict()
    divisor = int(inputs.get("OVERSAMPLE_DIV", state.get("OVERSAMPLE_DIV", 2)))
    if divisor < 1:
        divisor = 1
    if divisor > 64:
        divisor = 64
    state["OVERSAMPLE_DIV"] = divisor

    if int(inputs.get("rst", 0)) & 1:
        state["sync1"] = 1
        state["sync2"] = 1
        state["mode"] = 0
        state["offset"] = 0
        state["vote7"] = 0
        state["vote8"] = 0
        state["vote9"] = 0
        state["received"] = 0
        state["rx_data"] = 0
        outputs["rx_data"] = 0
        outputs["rx_strobe"] = 0
        outputs["frame_err"] = 0
        return state, outputs

    line = state.get("sync2", 1) & 1
    old_sync1 = state.get("sync1", 1) & 1
    state["sync1"] = int(inputs.get("rx", 0)) & 1
    state["sync2"] = old_sync1

    strobe = 0
    frame_err = 0
    mode = state.get("mode", 0)

    if mode == 0:
        if line == 0:
            state["mode"] = 1
            state["offset"] = 0
            state["vote7"] = 0
            state["vote8"] = 0
            state["vote9"] = 0
            state["received"] = 0
    elif mode == 1:
        offset = state.get("offset", 0) + 1
        state["offset"] = offset
        bit_index = offset // (16 * divisor)
        phase = offset % (16 * divisor)

        if phase == 7 * divisor:
            state["vote7"] = line
        elif phase == 8 * divisor:
            state["vote8"] = line
        elif phase == 9 * divisor:
            state["vote9"] = line
            majority = (state.get("vote7", 0) + state.get("vote8", 0) + line) >= 2

            if bit_index == 0:
                if majority:
                    state["mode"] = 0
                    state["offset"] = 0
                else:
                    state["received"] = 0
            elif bit_index >= 1 and bit_index <= 8:
                received = state.get("received", 0)
                if majority:
                    received = received | (1 << (bit_index - 1))
                else:
                    received = received & (~(1 << (bit_index - 1)))
                state["received"] = received & 255
            elif bit_index == 9:
                state["offset"] = 0
                if majority:
                    state["rx_data"] = state.get("received", 0) & 255
                    state["mode"] = 0
                    strobe = 1
                else:
                    state["mode"] = 2
                    frame_err = 1
    else:
        if line == 1:
            state["mode"] = 0
            state["offset"] = 0

    outputs["rx_data"] = state.get("rx_data", 0) & 255
    outputs["rx_strobe"] = strobe & 1
    outputs["frame_err"] = frame_err & 1
    return state, outputs