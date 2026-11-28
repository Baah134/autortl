def init():
    return dict()


def signed32(value):
    value = int(value) & 0xffffffff
    if value & 0x80000000:
        return value - 0x100000000
    return value


def step(state, inputs):
    rs1_val = int(inputs.get("rs1_val", 0)) & 0xffffffff
    rs2_val = int(inputs.get("rs2_val", 0)) & 0xffffffff
    pc_val = int(inputs.get("pc_val", 0)) & 0xffffffff
    imm = int(inputs.get("imm", 0)) & 0xffffffff
    a_sel = int(inputs.get("a_sel", 0)) & 0x3
    b_sel = int(inputs.get("b_sel", 0)) & 0x1
    op = int(inputs.get("op", 0)) & 0xf

    if a_sel == 0:
        a = rs1_val
    elif a_sel == 1:
        a = pc_val
    else:
        a = 0

    if b_sel == 1:
        b = imm
    else:
        b = rs2_val

    operation = op & 0x7
    if operation == 0:
        if op & 0x8:
            y = (a - b) & 0xffffffff
        else:
            y = (a + b) & 0xffffffff
    elif operation == 1:
        y = (a << (b & 0x1f)) & 0xffffffff
    elif operation == 2:
        y = int(signed32(a) < signed32(b))
    elif operation == 3:
        y = int(a < b)
    elif operation == 4:
        y = a ^ b
    elif operation == 5:
        shift = b & 0x1f
        if op & 0x8:
            y = (signed32(a) >> shift) & 0xffffffff
        else:
            y = a >> shift
    elif operation == 6:
        y = a | b
    else:
        y = a & b

    outputs = dict()
    outputs["y"] = y & 0xffffffff
    outputs["eq"] = int(rs1_val == rs2_val)
    outputs["lt"] = int(signed32(rs1_val) < signed32(rs2_val))
    outputs["ltu"] = int(rs1_val < rs2_val)
    return state, outputs