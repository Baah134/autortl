"""Independent reference models for the harness winners, written from the frozen
specifications in curriculum/*/design_spec.json, not from the harness's
generated oracles.

Each model consumes one transaction (IN_BYTES bytes, least significant first)
and returns its result (OUT_BYTES bytes, least significant first). `wrong()`
returns a deliberately incorrect variant for negative controls: a correct
hardware result must fail against it.
"""
from __future__ import annotations

import random


class Model:
    name = ""
    in_bytes = 1
    out_bytes = 1

    def __init__(self, wrong: bool = False):
        self.is_wrong = wrong
        self.reset()

    def reset(self):
        """Return to the state after a reset (stateless models: nothing)."""

    def step(self, tx: bytes) -> bytes:
        if len(tx) != self.in_bytes:
            raise ValueError(f"{self.name}: expected {self.in_bytes} input bytes, got {len(tx)}")
        result = self._compute(tx)
        if result < 0 or result >= 1 << (8 * self.out_bytes):
            raise ValueError(f"{self.name}: result {result} does not fit {self.out_bytes} bytes")
        return result.to_bytes(self.out_bytes, "little")

    def _compute(self, tx: bytes) -> int:
        raise NotImplementedError

    def leading(self) -> list[bytes]:
        """Edge-case transactions sent before the random ones."""
        return []

    def random_tx(self, rng: random.Random) -> bytes:
        return bytes(rng.randrange(256) for _ in range(self.in_bytes))

    def stimulus(self, rng: random.Random, count: int) -> list[bytes]:
        lead = self.leading()[:count]
        return lead + [self.random_tx(rng) for _ in range(count - len(lead))]


def _signed8(value: int) -> int:
    return value - 256 if value & 0x80 else value


class Fir4(Model):
    """y = 3x[n] - 5x[n-1] + 7x[n-2] - 2x[n-3]; signed 8-bit in, 13-bit out,
    sign-extended to 16 bits. History is cleared by reset and only advances
    on accepted samples."""
    name, in_bytes, out_bytes = "fir4", 1, 2

    def reset(self):
        self.history = [0, 0, 0]

    def _compute(self, tx):
        x = _signed8(tx[0])
        c2 = 6 if self.is_wrong else 7
        full = 3 * x - 5 * self.history[0] + c2 * self.history[1] - 2 * self.history[2]
        self.history = [x] + self.history[:2]
        y = full & 0x1FFF
        y = y - 0x2000 if y & 0x1000 else y
        return y & 0xFFFF

    def leading(self):
        return [bytes([b & 0xFF]) for b in (127, -128, 127, -128, -1, 0, -128, 127, -128, 127)]


class Dot4(Model):
    """Unsigned exact a0*b0 + a1*b1 + a2*b2 + a3*b3 (0..260100), 18 bits.
    Byte order a0, b0, a1, b1, a2, b2, a3, b3."""
    in_bytes, out_bytes = 8, 3

    def _compute(self, tx):
        pairs = [(tx[2 * i], tx[2 * i + 1]) for i in range(4)]
        if self.is_wrong:
            pairs = pairs[:3]                       # drops the a3*b3 term
        return sum(a * b for a, b in pairs)

    def leading(self):
        return [bytes([255] * 8), bytes(8), bytes([255, 1] * 4), bytes([1, 255] * 4),
                bytes([128] * 8), bytes([255, 255, 0, 0, 255, 255, 0, 0]),
                bytes([0, 0, 255, 255, 0, 0, 255, 255])]


class ElasticDot4(Dot4):
    name = "elastic_dot4"


class Dot4Pipeline(Dot4):
    name = "dot4_pipeline"


class IterativeDivider(Model):
    """Unsigned 8-bit: quotient = dividend // divisor, remainder = dividend % divisor.
    Divide by zero: quotient = 0xFF and remainder = the dividend.
    Byte 0 = dividend, byte 1 = divisor; result byte 0 = quotient, byte 1 = remainder."""
    name, in_bytes, out_bytes = "iterative_divider", 2, 2

    def _compute(self, tx):
        dividend, divisor = tx[0], tx[1]
        if divisor == 0:
            quotient, remainder = 0xFF, dividend
        else:
            quotient, remainder = dividend // divisor, dividend % divisor
        if self.is_wrong:
            remainder = (remainder + 1) & 0xFF
        return quotient | remainder << 8

    def leading(self):
        cases = [(0, 0), (255, 0), (1, 0), (255, 1), (255, 255), (0, 1), (0, 255),
                 (7, 7), (5, 9), (200, 13), (128, 2), (255, 16), (254, 255), (129, 128)]
        return [bytes(case) for case in cases]

    def random_tx(self, rng):
        divisor = 0 if rng.randrange(16) == 0 else rng.randrange(256)
        return bytes([rng.randrange(256), divisor])


class PacketFifo(Model):
    """Order-preserving identity on (data, last). Byte 0 = data; byte 1 is the
    last marker, and any nonzero value sets last. The result's byte 1 is 0 or 1."""
    name, in_bytes, out_bytes = "packet_fifo", 2, 2

    def _compute(self, tx):
        last = 1 if tx[1] else 0
        if self.is_wrong:
            last ^= 1
        return tx[0] | last << 8

    def leading(self):
        return [bytes([0, 0]), bytes([255, 1]), bytes([1, 0]), bytes([0, 1]), bytes([0xA5, 0x80]),
                bytes([0x5A, 0x02]), bytes([0xFF, 0xFF]), bytes([0x00, 0x40]), bytes([0xFF, 0])]

    def random_tx(self, rng):
        marker = 0 if rng.randrange(2) else rng.randrange(1, 256)
        return bytes([rng.randrange(256), marker])


class SyncFifo(Model):
    """Order-preserving identity on 8-bit words."""
    name, in_bytes, out_bytes = "sync_fifo", 1, 1

    def _compute(self, tx):
        return tx[0] ^ 1 if self.is_wrong else tx[0]

    def leading(self):
        return [bytes([b]) for b in (0x00, 0xFF, 0xA5, 0x5A, 0x01, 0x80, 0x7F, 0xFE)]


MODELS = {cls.name: cls for cls in (Fir4, ElasticDot4, Dot4Pipeline, IterativeDivider,
                                     PacketFifo, SyncFifo)}


def model_for(name: str, wrong: bool = False) -> Model:
    try:
        return MODELS[name](wrong=wrong)
    except KeyError:
        raise KeyError(f"no model for design {name!r}; known: {', '.join(MODELS)}") from None
