from typing import Optional
from remerkleable.complex import ( Container, ProgressiveList)
from ..base import (
    TransactionType, ChainId, uint64, GasAmount, ExecutionAddress,
    uint256, Hash32, ProgressiveList
)
from ..fees import BasicFeesPerGas
from ..signature import Secp256k1ExecutionSignature

class AccessTuple(Container):
    address:      ExecutionAddress
    storage_keys: ProgressiveList[Hash32]

# 0x01 BASIC
class RlpAccessListBasicTransactionPayload(
    ProgressiveContainer(active_fields=[1, 1, 1, 1, 1, 1, 1, 1, 1])
):
    type_:            TransactionType       # 0x01
    chain_id:         ChainId
    nonce:            uint64
    max_fees_per_gas: BasicFeesPerGas
    gas:              GasAmount
    to:               ExecutionAddress
    value:            uint256
    input_:           ProgressiveList
    access_list:      ProgressiveList[AccessTuple]


class RlpAccessListBasicTransaction(Container):
    payload:   RlpAccessListBasicTransactionPayload
    signature: Secp256k1ExecutionSignature


# 0x01 CREATE
class RlpAccessListCreateTransactionPayload(
    ProgressiveContainer(active_fields=[1, 1, 1, 1, 1, 0, 1, 1, 1])
):
    type_:            TransactionType       # 0x01
    chain_id:         ChainId
    nonce:            uint64
    max_fees_per_gas: BasicFeesPerGas
    gas:              GasAmount
    value:            uint256
    input_:           ProgressiveList
    access_list:      ProgressiveList[AccessTuple]


class RlpAccessListCreateTransaction(Container):
    payload:   RlpAccessListCreateTransactionPayload
    signature: Secp256k1ExecutionSignature
