def init():
    return dict()


def sign_extend(value, width):
    sign = 1 << (width - 1)
    if value & sign:
        value = value - (1 << width)
    return value & 0xFFFFFFFF


def step(state, inputs):
    instr = int(inputs.get("instr", 0)) & 0xFFFFFFFF

    rs1 = (instr >> 15) & 0x1F
    rs2 = (instr >> 20) & 0x1F
    rd = (instr >> 7) & 0x1F
    funct3 = (instr >> 12) & 0x7
    opcode = instr & 0x7F

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
        imm = sign_extend((instr >> 20) & 0xFFF, 12)
        if funct3 == 5:
            alu_op = (((instr >> 30) & 1) << 3) | funct3
        else:
            alu_op = funct3
    elif opcode == 0x37:
        kind = 0
        a_sel = 2
        b_sel = 1
        imm = instr & 0xFFFFF000
    elif opcode == 0x17:
        kind = 0
        a_sel = 1
        b_sel = 1
        imm = instr & 0xFFFFF000
    elif opcode == 0x6F:
        kind = 4
        a_sel = 1
        b_sel = 1
        value = (((instr >> 31) & 1) << 20)
        value |= (((instr >> 12) & 0xFF) << 12)
        value |= (((instr >> 20) & 1) << 11)
        value |= (((instr >> 21) & 0x3FF) << 1)
        imm = sign_extend(value, 21)
    elif opcode == 0x67:
        kind = 5
        b_sel = 1
        imm = sign_extend((instr >> 20) & 0xFFF, 12)
    elif opcode == 0x63:
        kind = 3
        a_sel = 1
        b_sel = 1
        value = (((instr >> 31) & 1) << 12)
        value |= (((instr >> 7) & 1) << 11)
        value |= (((instr >> 25) & 0x3F) << 5)
        value |= (((instr >> 8) & 0xF) << 1)
        imm = sign_extend(value, 13)
    elif opcode == 0x03:
        kind = 1
        b_sel = 1
        imm = sign_extend((instr >> 20) & 0xFFF, 12)
    elif opcode == 0x23:
        kind = 2
        b_sel = 1
        value = (((instr >> 25) & 0x7F) << 5) | ((instr >> 7) & 0x1F)
        imm = sign_extend(value, 12)

    outputs = dict()
    outputs["rs1"] = rs1
    outputs["rs2"] = rs2
    outputs["rd"] = rd
    outputs["imm"] = imm & 0xFFFFFFFF
    outputs["alu_op"] = alu_op & 0xF
    outputs["a_sel"] = a_sel & 0x3
    outputs["b_sel"] = b_sel & 0x1
    outputs["kind"] = kind & 0x7
    outputs["funct3"] = funct3

    return state, outputs