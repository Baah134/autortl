def init():
    return dict(mem=[0] * 64, imem_rdata=0)


def step(state, inputs):
    outputs = dict()

    if inputs.get("rst", 0):
        state["mem"] = [0] * 64
        state["imem_rdata"] = 0
    else:
        read_addr = int(inputs.get("imem_raddr", 0)) & 63
        state["imem_rdata"] = state["mem"][read_addr]

        if inputs.get("imem_we", 0):
            write_addr = int(inputs.get("imem_waddr", 0)) & 63
            write_data = int(inputs.get("imem_wdata", 0)) & 4294967295
            state["mem"][write_addr] = write_data

    outputs["imem_rdata"] = state["imem_rdata"] & 4294967295
    return state, outputs