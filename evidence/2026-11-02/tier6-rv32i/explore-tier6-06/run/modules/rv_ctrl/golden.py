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
        "ld_q": 0
    }


def step(state, inputs):
    old_state = state.get("state", 0)
    pc = state.get("pc", 0) & 0xffffffff
    npc = state.get("npc", 0) & 0xffffffff
    res = state.get("res", 0) & 0xffffffff
    sdata = state.get("sdata", 0) & 0xffffffff
    rd_q = state.get("rd_q", 0) & 0x1f
    wb_q = state.get("wb_q", 0) & 1
    st_q = state.get("st_q", 0) & 1
    ld_q = state.get("ld_q", 0) & 1

    run = int(inputs.get("run", 0)) & 1
    kind = int(inputs.get("kind", 0)) & 7
    funct3 = int(inputs.get("funct3", 0)) & 7
    rd = int(inputs.get("rd", 0)) & 0x1f
    y = int(inputs.get("y", 0)) & 0xffffffff
    eq = int(inputs.get("eq", 0)) & 1
    lt = int(inputs.get("lt", 0)) & 1
    ltu = int(inputs.get("ltu", 0)) & 1
    rs2_val = int(inputs.get("rs2_val", 0)) & 0xffffffff
    dmem_rdata = int(inputs.get("dmem_rdata", 0)) & 0xffffffff
    rst = int(inputs.get("rst", 0)) & 1

    if rst:
        next_state = init()
    else:
        next_state = {
            "state": old_state,
            "pc": pc,
            "npc": npc,
            "res": res,
            "sdata": sdata,
            "rd_q": rd_q,
            "wb_q": wb_q,
            "st_q": st_q,
            "ld_q": ld_q
        }

        if old_state == 0:
            if run:
                next_state["state"] = 1
        elif old_state == 1:
            next_state["state"] = 2
        elif old_state == 2:
            link = (pc + 4) & 0xffffffff
            taken = 0
            if funct3 == 0:
                taken = eq
            elif funct3 == 1:
                taken = 1 - eq
            elif funct3 == 4:
                taken = lt
            elif funct3 == 5:
                taken = 1 - lt
            elif funct3 == 6:
                taken = ltu
            elif funct3 == 7:
                taken = 1 - ltu

            next_state["wb_q"] = int(kind == 0 or kind == 1 or kind == 4 or kind == 5)
            next_state["st_q"] = int(kind == 2)
            next_state["ld_q"] = int(kind == 1)
            next_state["rd_q"] = rd
            next_state["sdata"] = rs2_val
            if kind == 4 or kind == 5:
                next_state["res"] = link
            else:
                next_state["res"] = y

            if kind == 4 or (kind == 3 and taken):
                next_state["npc"] = y
            elif kind == 5:
                next_state["npc"] = y & 0xfffffffe
            else:
                next_state["npc"] = link

            if kind == 1 or kind == 2:
                next_state["state"] = 3
            else:
                next_state["state"] = 5
        elif old_state == 3:
            if ld_q:
                next_state["state"] = 4
            else:
                next_state["state"] = 5
        elif old_state == 4:
            next_state["res"] = dmem_rdata
            next_state["state"] = 5
        elif old_state == 5:
            next_state["pc"] = npc
            next_state["state"] = 0
        else:
            next_state["state"] = 0

    current = next_state
    current_state = current["state"]
    current_pc = current["pc"] & 0xffffffff
    current_res = current["res"] & 0xffffffff
    current_sdata = current["sdata"] & 0xffffffff
    current_rd_q = current["rd_q"] & 0x1f
    current_wb_q = current["wb_q"] & 1
    current_st_q = current["st_q"] & 1

    outputs = {
        "pc": current_pc,
        "imem_raddr": (current_pc >> 2) & 0x3f,
        "retire": int(current_state == 5),
        "rf_we": int(current_state == 5 and current_wb_q),
        "rf_waddr": current_rd_q,
        "rf_wdata": current_res,
        "dmem_we": int(current_state == 3 and current_st_q),
        "dmem_addr": (current_res >> 2) & 0x1f,
        "dmem_wdata": current_sdata
    }
    return current, outputs