def init():
    return dict(ctrl_reg=0, scratch=0, config=0x00000100,
                irq_mask=0, irq_status=0, status=0,
                write_count=0)


def step(state, inputs):
    if inputs.get("rst", 0):
        state = init()
    else:
        wr_en = int(inputs.get("wr_en", 0)) & 1
        wr_idx = int(inputs.get("wr_idx", 0)) & 7
        wr_data = int(inputs.get("wr_data", 0)) & 0xFFFFFFFF
        wr_strb = int(inputs.get("wr_strb", 0)) & 15
        irq_set = int(inputs.get("irq_set", 0)) & 0xFF

        state["status"] = int(inputs.get("status_in", 0)) & 0xFFFFFFFF

        clear = 0
        if wr_en and wr_idx == 4 and (wr_strb & 1):
            clear = wr_data & 0xFF
        state["irq_status"] = (
            (state.get("irq_status", 0) & 0xFF & (~clear & 0xFF)) | irq_set
        ) & 0xFF

        if wr_en:
            state["write_count"] = (state.get("write_count", 0) + 1) & 0xFFFFFFFF

            if wr_idx == 0 or wr_idx == 1 or wr_idx == 2:
                key = "ctrl_reg"
                if wr_idx == 1:
                    key = "scratch"
                elif wr_idx == 2:
                    key = "config"
                value = state.get(key, 0) & 0xFFFFFFFF
                for byte in range(4):
                    if (wr_strb >> byte) & 1:
                        shift = byte * 8
                        mask = 255 << shift
                        value = (value & (~mask & 0xFFFFFFFF)) | (wr_data & mask)
                state[key] = value & 0xFFFFFFFF
            elif wr_idx == 3 and (wr_strb & 1):
                state["irq_mask"] = wr_data & 0xFF

    ctrl = state.get("ctrl_reg", 0) & 0xFFFFFFFF
    scratch = state.get("scratch", 0) & 0xFFFFFFFF
    config = state.get("config", 0) & 0xFFFFFFFF
    irq_mask = state.get("irq_mask", 0) & 0xFF
    irq_status = state.get("irq_status", 0) & 0xFF
    status = state.get("status", 0) & 0xFFFFFFFF
    write_count = state.get("write_count", 0) & 0xFFFFFFFF

    regs_flat = (
        ctrl
        | (scratch << 32)
        | (config << 64)
        | (irq_mask << 96)
        | (irq_status << 128)
        | (status << 160)
        | (0x52544C35 << 192)
        | (write_count << 224)
    ) & ((1 << 256) - 1)

    outputs = dict(
        regs_flat=regs_flat,
        ctrl=ctrl,
        irq=int(bool(irq_status & irq_mask))
    )
    return state, outputs