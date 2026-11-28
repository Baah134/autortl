def init():
    return dict(mem=[0, 0, 0, 0, 0, 0, 0, 0], rd_data=0)

def step(state, inputs):
    outputs = dict()
    if inputs.get("rst", 0):
        state["mem"] = [0, 0, 0, 0, 0, 0, 0, 0]
        state["rd_data"] = 0
    else:
        rd_addr = int(inputs.get("rd_addr", 0)) & 7
        state["rd_data"] = state["mem"][rd_addr] & 255
        if inputs.get("wr_en", 0):
            wr_addr = int(inputs.get("wr_addr", 0)) & 7
            wr_data = int(inputs.get("wr_data", 0)) & 255
            state["mem"][wr_addr] = wr_data
    outputs["rd_data"] = state["rd_data"] & 255
    return state, outputs