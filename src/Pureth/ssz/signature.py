from __future__ import annotations

from remerkleable.complex import ProgressiveContainer
from ..base import ByteVector, Hash32, ExecutionAddress
from ethereum_test_types import keccak  # or wherever you expose keccak256
try:
    from coincurve import PublicKey
except Exception:
    PublicKey = None  # soft dependency, used only by recover_signer()

SECP256K1_SIGNATURE_SIZE = 32 + 32 + 1
SECP256K1N = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16)


class Secp256k1ExecutionSignature(ProgressiveContainer(active_fields=[1])):
    secp256k1: ByteVector[SECP256K1_SIGNATURE_SIZE]


def secp256k1_pack(r: int, s: int, y_parity: int) -> bytes:
    return r.to_bytes(32, "big") + s.to_bytes(32, "big") + bytes([y_parity])


def secp256k1_unpack(signature: bytes) -> tuple[int, int, int]:
    assert len(signature) == SECP256K1_SIGNATURE_SIZE
    r = int.from_bytes(signature[0:32], "big")
    s = int.from_bytes(signature[32:64], "big")
    y_parity = signature[64]
    return r, s, y_parity


def secp256k1_validate(signature: bytes) -> None:
    r, s, y_parity = secp256k1_unpack(signature)
    assert 0 < r < SECP256K1N
    assert 0 < s <= SECP256K1N // 2
    assert y_parity in (0, 1)


def secp256k1_recover_signer(signature: bytes, sig_hash: Hash32) -> ExecutionAddress:
    """
    Best-effort recover; requires coincurve. If not available, raise.
    """
    if PublicKey is None:
        raise RuntimeError("coincurve is required for recover_signer")

    # coincurve expects compact (r||s, v). We already have that layout.
    rec_id = signature[64]
    if rec_id not in (0, 1):
        raise ValueError("y_parity must be 0/1 for raw ECDSA recover")

    pub = PublicKey.from_signature_and_message(signature, bytes(sig_hash), hasher=None)
    uncompressed = pub.format(compressed=False)
    return ExecutionAddress(keccak(uncompressed[1:])[-20:])
