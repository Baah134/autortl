def init():
    return dict()


def step(state, inputs):
    mask = 0xffffffff
    rs1_val = inputs.get("rs1_val", 0) & mask
    rs2_val = inputs.get("rs2_val", 0) & mask
    pc_val = inputs.get("pc_val", 0) & mask
    imm = inputs.get("imm", 0) & mask
    a_sel = inputs.get("a_sel", 0) & 3
    b_sel = inputs.get("b_sel", 0) & 1
    op = inputs.get("op", 0) & 15

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

    operation = op & 7
    if operation == 0:
        if op & 8:
            y = a - b
        else:
            y = a + b
    elif operation == 1:
        y = a << (b & 31)
    elif operation == 2:
        signed_a = a
        signed_b = b
        if a & 0x80000000:
            signed_a = a - 0x100000000
        if b & 0x80000000:
            signed_b = b - 0x100000000
        y = int(signed_a < signed_b)
    elif operation == 3:
        y = int(a < b)
    elif operation == 4:
        y = a ^ b
    elif operation == 5:
        shift = b & 31
        if op & 8:
            signed_a = a
            if a & 0x80000000:
                signed_a = a - 0x100000000
            y = signed_a >> shift
        else:
            y = a >> shift
    elif operation == 6:
        y = a | b
    else:
        y = a & b

    signed_rs1 = rs1_val
    if rs1_val & 0x80000000:
        signed_rs1 = rs1_val - 0x100000000
    signed_rs2 = rs2_val
    if rs2_val & 0x80000000:
        signed_rs2 = rs2_val - 0x100000000

    outputs = dict()
    outputs["y"] = y & mask
    outputs["eq"] = int(rs1_val == rs2_val)
    outputs["lt"] = int(signed_rs1 < signed_rs2)
    outputs["ltu"] = int(rs1_val < rs2_val)
    return state, outputs