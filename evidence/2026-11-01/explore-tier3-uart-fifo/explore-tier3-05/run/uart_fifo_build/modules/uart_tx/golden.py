def init():
    return dict(tx=1, active=0, bit_index=0, remaining=0, data=0)

def step(state, inputs):
    tx = state.get("tx", 1)
    active = state.get("active", 0)
    bit_index = state.get("bit_index", 0)
    remaining = state.get("remaining", 0)
    data = state.get("data", 0)
    div = max(1, int(inputs.get("DIV", 868)))

    if inputs.get("rst", 0):
        tx = 1
        active = 0
        bit_index = 0
        remaining = 0
        data = 0
    else:
        if active == 0:
            data = int(inputs.get("in_data", 0)) & 255
            tx = 0
            active = 1
            bit_index = -1
            remaining = div - 1
        elif remaining > 0:
            remaining = remaining - 1
        elif bit_index == -1:
            bit_index = 0
            tx = data & 1
            remaining = div - 1
        elif bit_index < 7:
            bit_index = bit_index + 1
            tx = (data >> bit_index) & 1
            remaining = div - 1
        elif bit_index == 7:
            bit_index = 8
            tx = 1
            remaining = div - 1
        else:
            tx = 1
            active = 0
            bit_index = 0
            remaining = 0

    state = dict(tx=tx, active=active, bit_index=bit_index, remaining=remaining, data=data)
    outputs = dict(tx=tx)
    return state, outputs