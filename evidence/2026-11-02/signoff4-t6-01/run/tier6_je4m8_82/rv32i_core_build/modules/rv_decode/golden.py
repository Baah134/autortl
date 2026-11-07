def init():
    return dict()


def sign_extend(value, width):
    sign = 1 << (width - 1)
    if value & sign:
        return value - (1 << width)
    return value


def step(state, inputs):
    instr = inputs.get("instr", 0) & 0xffffffff

    rs1 = (instr >> 15) & 0x1f
    rs2 = (instr >> 20) & 0x1f
    rd = (instr >> 7) & 0x1f
    funct3 = (instr >> 12) & 0x7
    opcode = instr & 0x7f

    imm = 0
    alu_op = 0
    a_sel = 0
    b_sel = 0
    kind = 6

    if opcode == 0x33:
        kind = 0
        alu_op = (((instr >> 30) & 1) << 3) | funct3
    elif opcode == 0x13:
        kind = 0
        b_sel = 1
        imm = sign_extend((instr >> 20) & 0xfff, 12) & 0xffffffff
        if funct3 == 5:
            alu_op = (((instr >> 30) & 1) << 3) | funct3
        else:
            alu_op = funct3
    elif opcode == 0x37:
        kind = 0
        a_sel = 2
        b_sel = 1
        imm = instr & 0xfffff000
    elif opcode == 0x17:
        kind = 0
        a_sel = 1
        b_sel = 1
        imm = instr & 0xfffff000
    elif opcode == 0x6f:
        kind = 4
        a_sel = 1
        b_sel = 1
        value = (((instr >> 31) & 1) << 20)
        value |= (((instr >> 12) & 0xff) << 12)
        value |= (((instr >> 20) & 1) << 11)
        value |= (((instr >> 21) & 0x3ff) << 1)
        imm = sign_extend(value, 21) & 0xffffffff
    elif opcode == 0x67:
        kind = 5
        b_sel = 1
        imm = sign_extend((instr >> 20) & 0xfff, 12) & 0xffffffff
    elif opcode == 0x63:
        kind = 3
        a_sel = 1
        b_sel = 1
        value = (((instr >> 31) & 1) << 12)
        value |= (((instr >> 7) & 1) << 11)
        value |= (((instr >> 25) & 0x3f) << 5)
        value |= (((instr >> 8) & 0xf) << 1)
        imm = sign_extend(value, 13) & 0xffffffff
    elif opcode == 0x03:
        kind = 1
        b_sel = 1
        imm = sign_extend((instr >> 20) & 0xfff, 12) & 0xffffffff
    elif opcode == 0x23:
        kind = 2
        b_sel = 1
        value = (((instr >> 25) & 0x7f) << 5) | ((instr >> 7) & 0x1f)
        imm = sign_extend(value, 12) & 0xffffffff

    outputs = dict()
    outputs["rs1"] = rs1
    outputs["rs2"] = rs2
    outputs["rd"] = rd
    outputs["imm"] = imm
    outputs["alu_op"] = alu_op
    outputs["a_sel"] = a_sel
    outputs["b_sel"] = b_sel
    outputs["kind"] = kind
    outputs["funct3"] = funct3
    return state, outputs