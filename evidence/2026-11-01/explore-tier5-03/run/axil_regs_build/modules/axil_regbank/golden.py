def init():
    regs = [0, 0, 0x00000100, 0, 0, 0, 0x52544C35, 0]
    return dict(regs=regs)


def step(state, inputs):
    regs = list(state.get("regs", [0, 0, 0x00000100, 0, 0, 0, 0x52544C35, 0]))

    rst = int(inputs.get("rst", 0)) & 1
    if rst:
        regs = [0, 0, 0x00000100, 0, 0, 0, 0x52544C35, 0]
    else:
        wr_en = int(inputs.get("wr_en", 0)) & 1
        wr_idx = int(inputs.get("wr_idx", 0)) & 0x7
        wr_data = int(inputs.get("wr_data", 0)) & 0xFFFFFFFF
        wr_strb = int(inputs.get("wr_strb", 0)) & 0xF
        irq_set = int(inputs.get("irq_set", 0)) & 0xFF
        status_in = int(inputs.get("status_in", 0)) & 0xFFFFFFFF

        regs[5] = status_in

        clear = 0
        if wr_en and wr_idx == 4 and (wr_strb & 1):
            clear = wr_data & 0xFF
        regs[4] = ((regs[4] & 0xFF & (~clear & 0xFF)) | irq_set) & 0xFF

        if wr_en:
            regs[7] = (regs[7] + 1) & 0xFFFFFFFF

            if wr_idx == 0 or wr_idx == 1 or wr_idx == 2:
                for byte_index in range(4):
                    if (wr_strb >> byte_index) & 1:
                        shift = byte_index * 8
                        byte_mask = 0xFF << shift
                        regs[wr_idx] = (regs[wr_idx] & (~byte_mask & 0xFFFFFFFF)) | (wr_data & byte_mask)
            elif wr_idx == 3 and (wr_strb & 1):
                regs[3] = wr_data & 0xFF

    state["regs"] = regs

    regs_flat = 0
    for index in range(8):
        regs_flat |= (regs[index] & 0xFFFFFFFF) << (32 * index)

    irq = 0
    if (regs[4] & regs[3] & 0xFF) != 0:
        irq = 1

    outputs = dict(
        regs_flat=regs_flat & ((1 << 256) - 1),
        ctrl=regs[0] & 0xFFFFFFFF,
        irq=irq
    )
    return state, outputs