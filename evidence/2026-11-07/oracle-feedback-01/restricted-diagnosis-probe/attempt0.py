def init():
    sbox = [0] * 256
    log = [0] * 256
    antilog = [0] * 512
    value = 1
    for i in range(255):
        antilog[i] = value
        log[value] = i
        value = value << 1
        if value & 256:
            value = value ^ 0x11b
    for i in range(255, 512):
        antilog[i] = antilog[i - 255]

    for x in range(256):
        if x == 0:
            inverse = 0
        else:
            inverse = antilog[255 - log[x]]
        y = inverse
        result = y
        for shift in range(1, 5):
            y = ((y << 1) | (y >> 7)) & 255
            result = result ^ y
        sbox[x] = result ^ 0x63

    rcon_table = [0] * 16
    rcon_table[0] = 1
    for i in range(1, 10):
        rcon_table[i] = rcon_table[i - 1] << 1
        if rcon_table[i] & 256:
            rcon_table[i] = rcon_table[i] ^ 0x11b
    return dict(
        busy=0,
        out_valid=0,
        rnd=0,
        ct=0,
        rk=0,
        sbox=sbox,
        rcon_table=rcon_table,
    )


def step(state, inputs):
    mask = 0xffffffff
    mask128 = (1 << 128) - 1
    busy = state.get("busy", 0)
    out_valid = state.get("out_valid", 0)
    rnd = state.get("rnd", 0)
    ct = state.get("ct", 0) & mask128
    rk = state.get("rk", 0) & mask128

    if inputs.get("rst", 0):
        state["busy"] = 0
        state["out_valid"] = 0
        state["rnd"] = 0
        state["ct"] = 0
        state["rk"] = 0
    else:
        if busy:
            if rnd == 0:
                state["rnd"] = 1
            else:
                sbox = state.get("sbox", [0] * 256)
                round_state = [0] * 16
                for i in range(16):
                    round_state[i] = (ct >> (120 - 8 * i)) & 255

                shifted = [0] * 16
                for row in range(4):
                    for col in range(4):
                        shifted[row + 4 * col] = round_state[row + 4 * ((col + row) % 4)]

                mixed = [0] * 16
                for col in range(4):
                    a0 = sbox[shifted[4 * col]]
                    a1 = sbox[shifted[1 + 4 * col]]
                    a2 = sbox[shifted[2 + 4 * col]]
                    a3 = sbox[shifted[3 + 4 * col]]
                    if rnd != 10:
                        mixed[4 * col] = ((a0 << 1) ^ (0x11b if a0 & 128 else 0) ^ (a1 << 1) ^ (0x11b if a1 & 128 else 0) ^ a1 ^ a2 ^ a3) & 255
                        mixed[1 + 4 * col] = (a0 ^ ((a1 << 1) ^ (0x11b if a1 & 128 else 0)) ^ (a2 << 1) ^ (0x11b if a2 & 128 else 0) ^ a2 ^ a3) & 255
                        mixed[2 + 4 * col] = (a0 ^ a1 ^ ((a2 << 1) ^ (0x11b if a2 & 128 else 0)) ^ (a3 << 1) ^ (0x11b if a3 & 128 else 0) ^ a3) & 255
                        mixed[3 + 4 * col] = (((a0 << 1) ^ (0x11b if a0 & 128 else 0)) ^ a0 ^ a1 ^ a2 ^ ((a3 << 1) ^ (0x11b if a3 & 128 else 0))) & 255
                    else:
                        mixed[4 * col] = a0
                        mixed[1 + 4 * col] = a1
                        mixed[2 + 4 * col] = a2
                        mixed[3 + 4 * col] = a3

                round_key = [0] * 16
                for i in range(16):
                    round_key[i] = (rk >> (120 - 8 * i)) & 255
                next_ct = 0
                for i in range(16):
                    byte_value = mixed[i] ^ round_key[i]
                    next_ct = (next_ct << 8) | byte_value
                ct = next_ct & mask128
                state["ct"] = ct

                if rnd == 10:
                    state["busy"] = 0
                    state["out_valid"] = 1
                    state["rnd"] = 0
                else:
                    state["rnd"] = rnd + 1

            key_bytes = [0] * 16
            for i in range(16):
                key_bytes[i] = (rk >> (120 - 8 * i)) & 255
            rotated = [key_bytes[13], key_bytes[14], key_bytes[15], key_bytes[12]]
            sbox = state.get("sbox", [0] * 256)
            rcon_table = state.get("rcon_table", [0] * 16)
            temp0 = sbox[rotated[0]] ^ rcon_table[rnd]
            temp1 = sbox[rotated[1]]
            temp2 = sbox[rotated[2]]
            temp3 = sbox[rotated[3]]
            next_key_bytes = [0] * 16
            next_key_bytes[0] = key_bytes[0] ^ temp0
            next_key_bytes[1] = key_bytes[1] ^ temp1
            next_key_bytes[2] = key_bytes[2] ^ temp2
            next_key_bytes[3] = key_bytes[3] ^ temp3
            for i in range(4, 16):
                next_key_bytes[i] = key_bytes[i] ^ next_key_bytes[i - 4]
            next_rk = 0
            for i in range(16):
                next_rk = (next_rk << 8) | next_key_bytes[i]
            state["rk"] = next_rk & mask128
        elif out_valid:
            if inputs.get("out_ready", 0):
                state["out_valid"] = 0
        elif inputs.get("in_valid", 0):
            state["ct"] = (inputs.get("pt", 0) ^ inputs.get("key", 0)) & mask128
            state["rk"] = inputs.get("key", 0) & mask128
            state["rnd"] = 0
            state["busy"] = 1

    busy = state.get("busy", 0)
    out_valid = state.get("out_valid", 0)
    rnd = state.get("rnd", 0)
    rcon_table = state.get("rcon_table", [0] * 16)
    return state, dict(
        in_ready=1 if not busy and not out_valid else 0,
        out_valid=out_valid,
        ct=state.get("ct", 0) & mask128,
        rk=state.get("rk", 0) & mask128,
        rcon=rcon_table[rnd] & 255,
        last=1 if rnd == 10 else 0,
    )