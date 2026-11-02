def init():
    return dict()


def step(state, inputs):
    mask = 0xffffffff
    a_sel = int(inputs.get("a_sel", 0)) & 3
    b_sel = int(inputs.get("b_sel", 0)) & 1
    op = int(inputs.get("op", 0)) & 15
    rs1_val = int(inputs.get("rs1_val", 0)) & mask
    rs2_val = int(inputs.get("rs2_val", 0)) & mask
    pc_val = int(inputs.get("pc_val", 0)) & mask
    imm = int(inputs.get("imm", 0)) & mask

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

    op_low = op & 7
    if op_low == 0:
        if op & 8:
            y = a - b
        else:
            y = a + b
    elif op_low == 1:
        y = a << (b & 31)
    elif op_low == 2:
        signed_a = a
        signed_b = b
        if a & 0x80000000:
            signed_a = a - 0x100000000
        if b & 0x80000000:
            signed_b = b - 0x100000000
        if signed_a < signed_b:
            y = 1
        else:
            y = 0
    elif op_low == 3:
        if a < b:
            y = 1
        else:
            y = 0
    elif op_low == 4:
        y = a ^ b
    elif op_low == 5:
        shift = b & 31
        if op & 8:
            signed_a = a
            if a & 0x80000000:
                signed_a = a - 0x100000000
            y = signed_a >> shift
        else:
            y = a >> shift
    elif op_low == 6:
        y = a | b
    else:
        y = a & b

    signed_rs1 = rs1_val
    signed_rs2 = rs2_val
    if rs1_val & 0x80000000:
        signed_rs1 = rs1_val - 0x100000000
    if rs2_val & 0x80000000:
        signed_rs2 = rs2_val - 0x100000000

    outputs = dict()
    outputs["y"] = y & mask
    outputs["eq"] = int(rs1_val == rs2_val)
    outputs["lt"] = int(signed_rs1 < signed_rs2)
    outputs["ltu"] = int(rs1_val < rs2_val)
    return state, outputs