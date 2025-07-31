# ethereum_test_types/Pureth/ssz/payloads/set_code.py
from remerkleable.complex import ProgressiveContainer, Container, CompatibleUnion, ProgressiveList
from ..base import (TransactionType, ChainId, uint64, GasAmount, ExecutionAddress,uint256)
from ..fees import BasicFeesPerGas
from .access_list import AccessTuple                    
from ..signature import Secp256k1ExecutionSignature

class RlpReplayableBasicAuthorizationPayload(
    ProgressiveContainer(active_fields=[1, 0, 1, 1])
):
    magic:   TransactionType     # 0x05
    address: ExecutionAddress
    nonce:   uint64


class RlpBasicAuthorizationPayload(
    ProgressiveContainer(active_fields=[1, 1, 1, 1])
):
    magic:    TransactionType    # 0x05
    chain_id: ChainId
    address:  ExecutionAddress
    nonce:    uint64


class RlpAuthorization(CompatibleUnion[
    RlpReplayableBasicAuthorizationPayload,
    RlpBasicAuthorizationPayload,
]):
    pass

class RlpSetCodeTransactionPayload(
    ProgressiveContainer(active_fields=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
):
    type_:                     TransactionType     # 0x04
    chain_id:                  ChainId
    nonce:                     uint64
    max_fees_per_gas:          BasicFeesPerGas
    gas:                       GasAmount
    to:                        ExecutionAddress
    value:                     uint256
    input_:                    ProgressiveList
    access_list:               ProgressiveList[AccessTuple]
    max_priority_fees_per_gas: BasicFeesPerGas
    authorization_list:        ProgressiveList[RlpAuthorization]


class RlpSetCodeTransaction(Container):
    payload:   RlpSetCodeTransactionPayload
    signature: Secp256k1ExecutionSignature
