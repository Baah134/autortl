def init():
    return dict(
        OVERSAMPLE_DIV=2,
        sync1=1,
        sync2=1,
        state="IDLE",
        offset=0,
        votes=0,
        received=0,
        rx_data=0,
        rx_strobe=0,
        frame_err=0
    )

def step(state, inputs):
    outputs = dict()
    d = state.get("OVERSAMPLE_DIV", 2)
    rx = int(inputs.get("rx", 0)) & 1
    rst = int(inputs.get("rst", 0)) & 1

    if rst:
        state["sync1"] = 1
        state["sync2"] = 1
        state["state"] = "IDLE"
        state["offset"] = 0
        state["votes"] = 0
        state["received"] = 0
        state["rx_data"] = 0
        state["rx_strobe"] = 0
        state["frame_err"] = 0
    else:
        line = state["sync2"]
        old_sync1 = state["sync1"]
        state["sync1"] = rx
        state["sync2"] = old_sync1
        state["rx_strobe"] = 0
        state["frame_err"] = 0

        if state["state"] == "IDLE":
            if line == 0:
                state["state"] = "BUSY"
                state["offset"] = 0
                state["votes"] = 0
                state["received"] = 0
        elif state["state"] == "WAIT_IDLE":
            if line == 1:
                state["state"] = "IDLE"
        else:
            offset = state["offset"] + 1
            state["offset"] = offset
            bit_index = offset // (16 * d)
            phase = offset % (16 * d)

            if phase == 7 * d:
                state["votes"] = line
            elif phase == 8 * d:
                state["votes"] = state["votes"] + line
            elif phase == 9 * d:
                majority = state["votes"] + line >= 2

                if bit_index == 0:
                    state["votes"] = 0
                    if majority:
                        state["state"] = "IDLE"
                        state["offset"] = 0
                        state["received"] = 0
                elif bit_index >= 1 and bit_index <= 8:
                    if majority:
                        state["received"] = state["received"] | (1 << (bit_index - 1))
                    state["votes"] = 0
                elif bit_index == 9:
                    state["state"] = "IDLE"
                    state["offset"] = 0
                    state["votes"] = 0
                    if majority:
                        state["rx_data"] = state["received"] & 255
                        state["rx_strobe"] = 1
                    else:
                        state["frame_err"] = 1
                        state["state"] = "WAIT_IDLE"

    outputs["rx_data"] = state["rx_data"] & 255
    outputs["rx_strobe"] = state["rx_strobe"] & 1
    outputs["frame_err"] = state["frame_err"] & 1
    return state, outputs