def init():
    return {
        "state": 0,
        "pc": 0,
        "npc": 0,
        "res": 0,
        "sdata": 0,
        "rd_q": 0,
        "wb_q": 0,
        "st_q": 0,
        "ld_q": 0,
    }


def step(state, inputs):
    if inputs.get("rst", 0):
        state["state"] = 0
        state["pc"] = 0
        state["npc"] = 0
        state["res"] = 0
        state["sdata"] = 0
        state["rd_q"] = 0
        state["wb_q"] = 0
        state["st_q"] = 0
        state["ld_q"] = 0
    else:
        current_state = state.get("state", 0)
        if current_state == 0:
            if inputs.get("run", 0):
                state["state"] = 1
        elif current_state == 1:
            state["state"] = 2
        elif current_state == 2:
            kind = int(inputs.get("kind", 0)) & 7
            funct3 = int(inputs.get("funct3", 0)) & 7
            pc_value = int(state.get("pc", 0)) & 4294967295
            y = int(inputs.get("y", 0)) & 4294967295
            link = (pc_value + 4) & 4294967295

            state["wb_q"] = int(kind == 0 or kind == 1 or kind == 4 or kind == 5)
            state["st_q"] = int(kind == 2)
            state["ld_q"] = int(kind == 1)
            state["rd_q"] = int(inputs.get("rd", 0)) & 31
            state["sdata"] = int(inputs.get("rs2_val", 0)) & 4294967295

            if kind == 4 or kind == 5:
                state["res"] = link
            else:
                state["res"] = y

            taken = 0
            if funct3 == 0:
                taken = int(bool(inputs.get("eq", 0)))
            elif funct3 == 1:
                taken = int(not bool(inputs.get("eq", 0)))
            elif funct3 == 4:
                taken = int(bool(inputs.get("lt", 0)))
            elif funct3 == 5:
                taken = int(not bool(inputs.get("lt", 0)))
            elif funct3 == 6:
                taken = int(bool(inputs.get("ltu", 0)))
            elif funct3 == 7:
                taken = int(not bool(inputs.get("ltu", 0)))

            if kind == 4 or (kind == 3 and taken):
                state["npc"] = y
            elif kind == 5:
                state["npc"] = y & 4294967294
            else:
                state["npc"] = link

            if kind == 1 or kind == 2:
                state["state"] = 3
            else:
                state["state"] = 5
        elif current_state == 3:
            if state.get("ld_q", 0):
                state["state"] = 4
            else:
                state["state"] = 5
        elif current_state == 4:
            state["res"] = int(inputs.get("dmem_rdata", 0)) & 4294967295
            state["state"] = 5
        elif current_state == 5:
            state["pc"] = int(state.get("npc", 0)) & 4294967295
            state["state"] = 0
        else:
            state["state"] = 0

    pc_value = int(state.get("pc", 0)) & 4294967295
    res_value = int(state.get("res", 0)) & 4294967295
    current_state = state.get("state", 0)
    wb_q = int(state.get("wb_q", 0)) & 1
    st_q = int(state.get("st_q", 0)) & 1

    outputs = {
        "pc": pc_value,
        "imem_raddr": (pc_value >> 2) & 63,
        "retire": int(current_state == 5),
        "rf_we": int(current_state == 5 and wb_q != 0),
        "rf_waddr": int(state.get("rd_q", 0)) & 31,
        "rf_wdata": res_value,
        "dmem_we": int(current_state == 3 and st_q != 0),
        "dmem_addr": (res_value >> 2) & 31,
        "dmem_wdata": int(state.get("sdata", 0)) & 4294967295,
    }
    return state, outputs