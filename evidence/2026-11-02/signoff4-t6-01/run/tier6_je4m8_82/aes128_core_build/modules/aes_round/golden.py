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


def rotl8(value, count):
    return ((value << count) | (value >> (8 - count))) & 255


def init():
    exp_table = []
    log_table = [0] * 256
    value = 1
    for i in range(255):
        exp_table.append(value)
        log_table[value] = i
        value = gf_mul(value, 3)

    sbox = []
    for byte in range(256):
        if byte == 0:
            inverse = 0
        else:
            inverse = exp_table[255 - log_table[byte]]
        mapped = inverse ^ rotl8(inverse, 1) ^ rotl8(inverse, 2)
        mapped = mapped ^ rotl8(inverse, 3) ^ rotl8(inverse, 4) ^ 99
        sbox.append(mapped)

    return dict(sbox=sbox)


def step(state, inputs):
    sbox = state.get("sbox")
    state_value = int(inputs.get("state_in", 0)) & ((1 << 128) - 1)
    key_value = int(inputs.get("round_key", 0)) & ((1 << 128) - 1)
    final_round = int(inputs.get("final_round", 0)) & 1

    substituted = [0] * 16
    for n in range(16):
        byte = (state_value >> (120 - 8 * n)) & 255
        substituted[n] = sbox[byte]

    shifted = [0] * 16
    for column in range(4):
        for row in range(4):
            source_column = (column + row) % 4
            shifted[row + 4 * column] = substituted[row + 4 * source_column]

    if final_round == 0:
        mixed = [0] * 16
        for column in range(4):
            a0 = shifted[4 * column]
            a1 = shifted[1 + 4 * column]
            a2 = shifted[2 + 4 * column]
            a3 = shifted[3 + 4 * column]

            x0 = ((a0 << 1) & 255) ^ (27 if a0 & 128 else 0)
            x1 = ((a1 << 1) & 255) ^ (27 if a1 & 128 else 0)
            x2 = ((a2 << 1) & 255) ^ (27 if a2 & 128 else 0)
            x3 = ((a3 << 1) & 255) ^ (27 if a3 & 128 else 0)

            mixed[4 * column] = x0 ^ x1 ^ a1 ^ a2 ^ a3
            mixed[1 + 4 * column] = a0 ^ x1 ^ x2 ^ a2 ^ a3
            mixed[2 + 4 * column] = a0 ^ a1 ^ x2 ^ x3 ^ a3
            mixed[3 + 4 * column] = x0 ^ a0 ^ a1 ^ a2 ^ x3
        transformed = mixed
    else:
        transformed = shifted

    output_value = 0
    for n in range(16):
        key_byte = (key_value >> (120 - 8 * n)) & 255
        output_value = (output_value << 8) | (transformed[n] ^ key_byte)

    outputs = dict(state_out=output_value & ((1 << 128) - 1))
    return state, outputs