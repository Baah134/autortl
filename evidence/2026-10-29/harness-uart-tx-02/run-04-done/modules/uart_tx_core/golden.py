def init():
    return dict(busy=0, remaining=0, bit_index=0, data=0, div=868, tx=1, in_ready=1)

def step(state, inputs):
    rst = int(inputs.get("rst", 0))
    if rst:
        state["busy"] = 0
        state["remaining"] = 0
        state["bit_index"] = 0
        state["data"] = 0
        state["tx"] = 1
        state["in_ready"] = 1
    elif state.get("busy", 0):
        remaining = state.get("remaining", 0)
        if remaining > 1:
            state["remaining"] = remaining - 1
        else:
            bit_index = state.get("bit_index", 0)
            if bit_index == 9:
                state["busy"] = 0
                state["remaining"] = 0
                state["tx"] = 1
                state["in_ready"] = 1
            else:
                bit_index = bit_index + 1
                state["bit_index"] = bit_index
                if bit_index <= 8:
                    state["tx"] = (state.get("data", 0) >> (bit_index - 1)) & 1
                else:
                    state["tx"] = 1
                state["remaining"] = state.get("div", 868)
    elif int(inputs.get("in_valid", 0)) and int(state.get("in_ready", 1)):
        div = int(inputs.get("DIV", state.get("div", 868)))
        state["busy"] = 1
        state["div"] = div
        state["remaining"] = div
        state["bit_index"] = 0
        state["data"] = int(inputs.get("in_data", 0)) & 255
        state["tx"] = 0
        state["in_ready"] = 0

    outputs = dict(in_ready=int(state.get("in_ready", 1)) & 1, tx=int(state.get("tx", 1)) & 1)
    return state, outputs