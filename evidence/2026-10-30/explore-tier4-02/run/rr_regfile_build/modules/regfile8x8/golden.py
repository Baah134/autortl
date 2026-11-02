def init():
    return dict(mem=[0, 0, 0, 0, 0, 0, 0, 0], rd_data=0)

def step(state, inputs):
    mem = state.get("mem", [0, 0, 0, 0, 0, 0, 0, 0]).copy()
    rd_data = state.get("rd_data", 0) & 255

    if inputs.get("rst", 0):
        mem = [0, 0, 0, 0, 0, 0, 0, 0]
        rd_data = 0
    else:
        rd_addr = inputs.get("rd_addr", 0) & 7
        rd_data = mem[rd_addr] & 255

        if inputs.get("wr_en", 0):
            wr_addr = inputs.get("wr_addr", 0) & 7
            wr_data = inputs.get("wr_data", 0) & 255
            mem[wr_addr] = wr_data

    state = dict(mem=mem, rd_data=rd_data)
    outputs = dict(rd_data=rd_data)
    return state, outputs