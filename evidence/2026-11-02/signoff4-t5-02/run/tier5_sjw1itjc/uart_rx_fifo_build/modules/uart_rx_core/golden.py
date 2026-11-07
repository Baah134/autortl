def init():
    return dict(
        D=2,
        sync1=1,
        sync2=1,
        state=0,
        offset=0,
        votes=0,
        bits=0,
        rx_data=0,
        rx_strobe=0,
        frame_err=0
    )


def step(state, inputs):
    d = int(inputs.get("OVERSAMPLE_DIV", state.get("D", 2)))
    rx = int(inputs.get("rx", 0)) & 1
    rst = int(inputs.get("rst", 0)) & 1

    if rst:
        state["D"] = d
        state["sync1"] = 1
        state["sync2"] = 1
        state["state"] = 0
        state["offset"] = 0
        state["votes"] = 0
        state["bits"] = 0
        state["rx_data"] = 0
        state["rx_strobe"] = 0
        state["frame_err"] = 0
    else:
        line = state.get("sync2", 1)
        old_sync1 = state.get("sync1", 1)
        state["sync1"] = rx
        state["sync2"] = old_sync1
        state["D"] = d
        state["rx_strobe"] = 0
        state["frame_err"] = 0

        if state.get("state", 0) == 0:
            if line == 0:
                state["state"] = 1
                state["offset"] = 0
                state["votes"] = 0
                state["bits"] = 0
        elif state.get("state", 0) == 1:
            offset = state.get("offset", 0) + 1
            state["offset"] = offset
            bit_index = offset // (16 * d)
            phase = offset % (16 * d)

            if phase == 7 * d:
                state["votes"] = line
            elif phase == 8 * d:
                state["votes"] = state.get("votes", 0) + line
            elif phase == 9 * d:
                majority = state.get("votes", 0) + line >= 2
                state["votes"] = 0

                if bit_index == 0:
                    if majority:
                        state["state"] = 0
                        state["offset"] = 0
                elif 1 <= bit_index <= 8:
                    if majority:
                        state["bits"] = state.get("bits", 0) | (1 << (bit_index - 1))
                elif bit_index == 9:
                    state["offset"] = 0
                    if majority:
                        state["rx_data"] = state.get("bits", 0) & 255
                        state["rx_strobe"] = 1
                        state["state"] = 0
                    else:
                        state["frame_err"] = 1
                        state["state"] = 2
        else:
            if line == 1:
                state["state"] = 0
                state["offset"] = 0
                state["votes"] = 0

    outputs = dict(
        rx_data=state.get("rx_data", 0) & 255,
        rx_strobe=state.get("rx_strobe", 0) & 1,
        frame_err=state.get("frame_err", 0) & 1
    )
    return state, outputs