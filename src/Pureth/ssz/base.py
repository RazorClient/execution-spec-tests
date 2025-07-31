# ethereum_test_types/Pureth/ssz/base.py
from remerkleable.basic import (
    uint8, uint64, uint256,
    Bytes20, Bytes32, Bytes48
)
from remerkleable.complex import ByteVector, List, Container, Vector, ProgressiveList

TransactionType   = uint8
ChainId           = uint256
GasAmount         = uint64
ExecutionAddress  = Bytes20
Hash32            = Bytes32
VersionedHash     = Bytes32
KZGCommitment     = Bytes48
KZGProof          = Bytes48
SECP256K1_SIGNATURE_SIZE = 65      # 32 + 32 + 1

__all__ = [
    "Container", "List", "Vector", "ByteVector"," ProgressiveList"
    "uint8", "uint64", "uint256",
    "Bytes20", "Bytes32", "Bytes48",
    "TransactionType", "ChainId", "GasAmount",
    "ExecutionAddress", "Hash32", "VersionedHash",
    "KZGCommitment", "KZGProof", "SECP256K1_SIGNATURE_SIZE",
]
