def init():
    return dict(busy=0, phase=0, count=0, data=0, clks_per_bit=16)

def step(state, inputs):
    state = state.copy()
    outputs = dict()

    if int(inputs.get("rst", 0)) != 0:
        state = init()
    else:
        clks_per_bit = int(inputs.get("CLKS_PER_BIT", state.get("clks_per_bit", 16)))
        state["clks_per_bit"] = clks_per_bit
        ready = state.get("busy", 0) == 0 or state.get("phase", 0) == 9

        if ready and int(inputs.get("tx_valid", 0)) != 0:
            state["busy"] = 1
            state["phase"] = 0
            state["count"] = 0
            state["data"] = int(inputs.get("tx_data", 0)) & 255
        elif state.get("busy", 0) != 0:
            if state.get("count", 0) == clks_per_bit - 1:
                state["count"] = 0
                if state.get("phase", 0) == 9:
                    state["busy"] = 0
                    state["phase"] = 0
                else:
                    state["phase"] = state.get("phase", 0) + 1
            else:
                state["count"] = state.get("count", 0) + 1

    tx = 1
    if state.get("busy", 0) != 0:
        phase = state.get("phase", 0)
        if phase == 0:
            tx = 0
        elif phase <= 8:
            tx = (state.get("data", 0) >> (phase - 1)) & 1

    outputs["tx_ready"] = int(state.get("busy", 0) == 0 or state.get("phase", 0) == 9)
    outputs["tx"] = tx
    return state, outputs