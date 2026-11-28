def init():
    return dict()


def step(state, inputs):
    instr = int(inputs.get("instr", 0)) & 0xffffffff

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
        imm = (instr >> 20) & 0xfff
        if imm & 0x800:
            imm |= 0xfffff000
        alu_op = ((((instr >> 30) & 1) << 3) | funct3) if funct3 == 5 else funct3
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
        value = (((instr >> 31) & 1) << 20) | (((instr >> 12) & 0xff) << 12) | (((instr >> 20) & 1) << 11) | (((instr >> 21) & 0x3ff) << 1)
        if value & 0x100000:
            value |= 0xffe00000
        imm = value
    elif opcode == 0x67:
        kind = 5
        b_sel = 1
        imm = (instr >> 20) & 0xfff
        if imm & 0x800:
            imm |= 0xfffff000
    elif opcode == 0x63:
        kind = 3
        a_sel = 1
        b_sel = 1
        value = (((instr >> 31) & 1) << 12) | (((instr >> 7) & 1) << 11) | (((instr >> 25) & 0x3f) << 5) | (((instr >> 8) & 0xf) << 1)
        if value & 0x1000:
            value |= 0xffffe000
        imm = value
    elif opcode == 0x03:
        kind = 1
        b_sel = 1
        imm = (instr >> 20) & 0xfff
        if imm & 0x800:
            imm |= 0xfffff000
    elif opcode == 0x23:
        kind = 2
        b_sel = 1
        value = (((instr >> 25) & 0x7f) << 5) | ((instr >> 7) & 0x1f)
        if value & 0x800:
            value |= 0xfffff000
        imm = value

    if int(inputs.get("rst", 0)) & 1:
        imm = 0
        alu_op = 0
        a_sel = 0
        b_sel = 0
        kind = 6

    outputs = dict()
    outputs["rs1"] = rs1 & 0x1f
    outputs["rs2"] = rs2 & 0x1f
    outputs["rd"] = rd & 0x1f
    outputs["imm"] = imm & 0xffffffff
    outputs["alu_op"] = alu_op & 0xf
    outputs["a_sel"] = a_sel & 0x3
    outputs["b_sel"] = b_sel & 1
    outputs["kind"] = kind & 0x7
    outputs["funct3"] = funct3 & 0x7
    return state, outputs