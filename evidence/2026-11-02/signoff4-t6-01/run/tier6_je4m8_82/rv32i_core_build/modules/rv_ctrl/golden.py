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
    next_state = state.copy()

    if inputs.get("rst", 0):
        next_state = init()
    else:
        current = state.get("state", 0)

        if current == 0:
            if inputs.get("run", 0):
                next_state["state"] = 1
        elif current == 1:
            next_state["state"] = 2
        elif current == 2:
            kind = inputs.get("kind", 0) & 7
            funct3 = inputs.get("funct3", 0) & 7
            pc = state.get("pc", 0) & 4294967295
            link = (pc + 4) & 4294967295
            y = inputs.get("y", 0) & 4294967295

            eq = bool(inputs.get("eq", 0) & 1)
            lt = bool(inputs.get("lt", 0) & 1)
            ltu = bool(inputs.get("ltu", 0) & 1)

            taken = False
            if funct3 == 0:
                taken = eq
            elif funct3 == 1:
                taken = not eq
            elif funct3 == 4:
                taken = lt
            elif funct3 == 5:
                taken = not lt
            elif funct3 == 6:
                taken = ltu
            elif funct3 == 7:
                taken = not ltu

            next_state["wb_q"] = int(kind in (0, 1, 4, 5))
            next_state["st_q"] = int(kind == 2)
            next_state["ld_q"] = int(kind == 1)
            next_state["rd_q"] = inputs.get("rd", 0) & 31
            next_state["sdata"] = inputs.get("rs2_val", 0) & 4294967295

            if kind in (4, 5):
                next_state["res"] = link
            else:
                next_state["res"] = y

            if kind == 4 or (kind == 3 and taken):
                next_state["npc"] = y
            elif kind == 5:
                next_state["npc"] = y & 4294967294
            else:
                next_state["npc"] = link

            if kind in (1, 2):
                next_state["state"] = 3
            else:
                next_state["state"] = 5
        elif current == 3:
            if state.get("ld_q", 0):
                next_state["state"] = 4
            else:
                next_state["state"] = 5
        elif current == 4:
            next_state["res"] = inputs.get("dmem_rdata", 0) & 4294967295
            next_state["state"] = 5
        elif current == 5:
            next_state["pc"] = state.get("npc", 0) & 4294967295
            next_state["state"] = 0
        else:
            next_state["state"] = 0

    pc = next_state["pc"] & 4294967295
    res = next_state["res"] & 4294967295
    output = {
        "pc": pc,
        "imem_raddr": (pc >> 2) & 63,
        "retire": int(next_state["state"] == 5),
        "rf_we": int(next_state["state"] == 5 and next_state["wb_q"]),
        "rf_waddr": next_state["rd_q"] & 31,
        "rf_wdata": res,
        "dmem_we": int(next_state["state"] == 3 and next_state["st_q"]),
        "dmem_addr": (res >> 2) & 31,
        "dmem_wdata": next_state["sdata"] & 4294967295
    }
    return next_state, output