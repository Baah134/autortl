def init():
    return dict(regs=[0, 0, 0x00000100, 0, 0, 0, 0x52544C35, 0])


def step(state, inputs):
    regs = state.get("regs", [0, 0, 0x00000100, 0, 0, 0, 0x52544C35, 0]).copy()

    if inputs.get("rst", 0) & 1:
        regs = [0, 0, 0x00000100, 0, 0, 0, 0x52544C35, 0]
    else:
        wr_en = inputs.get("wr_en", 0) & 1
        wr_idx = inputs.get("wr_idx", 0) & 0x7
        wr_data = inputs.get("wr_data", 0) & 0xFFFFFFFF
        wr_strb = inputs.get("wr_strb", 0) & 0xF
        irq_set = inputs.get("irq_set", 0) & 0xFF

        if wr_en:
            regs[7] = (regs[7] + 1) & 0xFFFFFFFF

            if wr_idx <= 2:
                for lane in range(4):
                    if (wr_strb >> lane) & 1:
                        mask = 0xFF << (8 * lane)
                        regs[wr_idx] = (regs[wr_idx] & ~mask) | (wr_data & mask)
            elif wr_idx == 3 and (wr_strb & 1):
                regs[3] = wr_data & 0xFF

        clear = 0
        if wr_en and wr_idx == 4 and (wr_strb & 1):
            clear = wr_data & 0xFF
        regs[4] = ((regs[4] & 0xFF) & (~clear & 0xFF)) | irq_set
        regs[4] &= 0xFF

        regs[5] = inputs.get("status_in", 0) & 0xFFFFFFFF

    flat = 0
    for index in range(8):
        flat |= (regs[index] & 0xFFFFFFFF) << (32 * index)

    irq = 1 if ((regs[4] & regs[3] & 0xFF) != 0) else 0
    outputs = dict(regs_flat=flat, ctrl=regs[0] & 0xFFFFFFFF, irq=irq)
    state["regs"] = regs
    return state, outputs