def init():
    return {"regs": [0, 0, 0x00000100, 0, 0, 0, 0x52544C35, 0]}


def step(state, inputs):
    regs = state.get("regs", [0, 0, 0x00000100, 0, 0, 0, 0x52544C35, 0]).copy()

    if inputs.get("rst", 0):
        regs = [0, 0, 0x00000100, 0, 0, 0, 0x52544C35, 0]
    else:
        wr_en = inputs.get("wr_en", 0)
        wr_idx = inputs.get("wr_idx", 0) & 0x7
        wr_data = inputs.get("wr_data", 0) & 0xFFFFFFFF
        wr_strb = inputs.get("wr_strb", 0) & 0xF
        irq_set = inputs.get("irq_set", 0) & 0xFF

        regs[5] = inputs.get("status_in", 0) & 0xFFFFFFFF

        clear = 0
        if wr_en and wr_idx == 4 and (wr_strb & 1):
            clear = wr_data & 0xFF
        regs[4] = ((regs[4] & 0xFF & (~clear & 0xFF)) | irq_set) & 0xFF

        if wr_en:
            regs[7] = (regs[7] + 1) & 0xFFFFFFFF

            if wr_idx <= 2:
                for b in range(4):
                    if (wr_strb >> b) & 1:
                        mask = 0xFF << (8 * b)
                        regs[wr_idx] = (regs[wr_idx] & (~mask & 0xFFFFFFFF)) | (wr_data & mask)
            elif wr_idx == 3 and (wr_strb & 1):
                regs[3] = wr_data & 0xFF

    state["regs"] = regs

    regs_flat = 0
    for i in range(8):
        regs_flat |= (regs[i] & 0xFFFFFFFF) << (32 * i)

    outputs = {
        "regs_flat": regs_flat & ((1 << 256) - 1),
        "ctrl": regs[0] & 0xFFFFFFFF,
        "irq": int(bool((regs[4] & regs[3]) & 0xFF)),
    }
    return state, outputs