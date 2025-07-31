# ssz/payloads/fee_market.py
from typing import Optional
from remerkleable.complex import StableContainer, Profile, Container
from ..base import ( TransactionType, ChainId, uint64, GasAmount, ExecutionAddress,uint256, Hash32)
from ..fees import BasicFeesPerGas
from ..signature import Secp256k1ExecutionSignature
from .access_list import AccessTuple

# 0x02 BASIC (to present)
class RlpBasicTransactionPayload(
    ProgressiveContainer(active_fields=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
):
    type_:                     TransactionType    # 0x02
    chain_id:                  ChainId
    nonce:                     uint64
    max_fees_per_gas:          BasicFeesPerGas
    gas:                       GasAmount
    to:                        ExecutionAddress
    value:                     uint256
    input_:                    ProgressiveList
    access_list:               ProgressiveList[AccessTuple]
    max_priority_fees_per_gas: BasicFeesPerGas


class RlpBasicTransaction(Container):
    payload:   RlpBasicTransactionPayload
    signature: Secp256k1ExecutionSignature


# 0x02 CREATE (to absent)
class RlpCreateTransactionPayload(
    ProgressiveContainer(active_fields=[1, 1, 1, 1, 1, 0, 1, 1, 1, 1])
):
    type_:                     TransactionType    # 0x02
    chain_id:                  ChainId
    nonce:                     uint64
    max_fees_per_gas:          BasicFeesPerGas
    gas:                       GasAmount
    value:                     uint256
    input_:                    ProgressiveList
    access_list:               ProgressiveList[AccessTuple]
    max_priority_fees_per_gas: BasicFeesPerGas


class RlpCreateTransaction(Container):
    payload:   RlpCreateTransactionPayload
    signature: Secp256k1ExecutionSignature