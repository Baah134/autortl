def init():
    return dict(
        sync1=1,
        sync2=1,
        state="IDLE",
        offset=0,
        votes=[],
        data=0,
        rx_data=0,
        rx_strobe=0,
        frame_err=0,
        D=2
    )


def step(state, inputs):
    rx = int(inputs.get("rx", 0)) & 1
    rst = int(inputs.get("rst", 0)) & 1
    D = int(inputs.get("OVERSAMPLE_DIV", state["D"]))
    state["D"] = D

    outputs = dict()
    if rst:
        state["sync1"] = 1
        state["sync2"] = 1
        state["state"] = "IDLE"
        state["offset"] = 0
        state["votes"] = []
        state["data"] = 0
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
                state["votes"] = []
                state["data"] = 0
        elif state["state"] == "WAIT_IDLE":
            if line == 1:
                state["state"] = "IDLE"
        else:
            offset = state["offset"] + 1
            state["offset"] = offset
            bit_index = offset // (16 * D)
            phase = offset % (16 * D)

            if phase == 7 * D:
                state["votes"] = [line]
            elif phase == 8 * D:
                state["votes"].append(line)
            elif phase == 9 * D:
                majority = 1 if sum(state["votes"]) + line >= 2 else 0
                state["votes"] = []

                if bit_index == 0:
                    if majority == 1:
                        state["state"] = "IDLE"
                elif bit_index <= 8:
                    bit_position = bit_index - 1
                    if majority == 1:
                        state["data"] = state["data"] | (1 << bit_position)
                    else:
                        state["data"] = state["data"] & (255 ^ (1 << bit_position))
                elif bit_index == 9:
                    state["state"] = "IDLE"
                    if majority == 1:
                        state["rx_data"] = state["data"] & 255
                        state["rx_strobe"] = 1
                    else:
                        state["frame_err"] = 1
                        state["state"] = "WAIT_IDLE"

    outputs["rx_data"] = state["rx_data"] & 255
    outputs["rx_strobe"] = state["rx_strobe"] & 1
    outputs["frame_err"] = state["frame_err"] & 1
    return state, outputs