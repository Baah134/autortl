def gf_mul(a, b):
    result = 0
    for i in range(8):
        if b & 1:
            result = result ^ a
        high = a & 128
        a = (a << 1) & 255
        if high:
            a = a ^ 27
        b = b >> 1
    return result


def rotl8(value, amount):
    return ((value << amount) | (value >> (8 - amount))) & 255


def init():
    exp_table = []
    log_table = [0] * 256
    value = 1
    for i in range(255):
        exp_table.append(value)
        log_table[value] = i
        value = gf_mul(value, 3)

    sbox = []
    for x in range(256):
        if x == 0:
            inverse = 0
        else:
            inverse = exp_table[(255 - log_table[x]) % 255]
        mapped = inverse ^ rotl8(inverse, 1) ^ rotl8(inverse, 2)
        mapped = mapped ^ rotl8(inverse, 3) ^ rotl8(inverse, 4) ^ 99
        sbox.append(mapped)

    return dict(sbox=sbox)


def step(state, inputs):
    state_in = int(inputs.get("state_in", 0)) & ((1 << 128) - 1)
    round_key = int(inputs.get("round_key", 0)) & ((1 << 128) - 1)
    final_round = int(inputs.get("final_round", 0)) & 1

    source = []
    for n in range(16):
        shift = 120 - 8 * n
        source.append((state_in >> shift) & 255)

    substituted = []
    for n in range(16):
        substituted.append(state["sbox"][source[n]])

    shifted = [0] * 16
    for column in range(4):
        for row in range(4):
            old_column = (column + row) % 4
            shifted[row + 4 * column] = substituted[row + 4 * old_column]

    if final_round == 0:
        mixed = [0] * 16
        for column in range(4):
            a0 = shifted[4 * column]
            a1 = shifted[1 + 4 * column]
            a2 = shifted[2 + 4 * column]
            a3 = shifted[3 + 4 * column]
            mixed[4 * column] = gf_mul(a0, 2) ^ gf_mul(a1, 3) ^ a2 ^ a3
            mixed[1 + 4 * column] = a0 ^ gf_mul(a1, 2) ^ gf_mul(a2, 3) ^ a3
            mixed[2 + 4 * column] = a0 ^ a1 ^ gf_mul(a2, 2) ^ gf_mul(a3, 3)
            mixed[3 + 4 * column] = gf_mul(a0, 3) ^ a1 ^ a2 ^ gf_mul(a3, 2)
        result_bytes = mixed
    else:
        result_bytes = shifted

    result = 0
    for n in range(16):
        result = (result << 8) | result_bytes[n]

    outputs = dict(state_out=(result ^ round_key) & ((1 << 128) - 1))
    return state, outputs