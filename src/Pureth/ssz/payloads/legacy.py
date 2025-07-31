from typing import Optional
from ..base import TransactionType, ChainId, uint64, GasAmount, ExecutionAddress, uint256
from ..fees import BasicFeesPerGas
from ..signature import Secp256k1ExecutionSignature
from remerkleable.complex import ProgressiveContainer, Container, ProgressiveList

# Replayable BASIC
class RlpLegacyReplayableBasicTransactionPayload(
    ProgressiveContainer(active_fields=[1, 0, 1, 1, 1, 1, 1, 1])
):
    type_:            TransactionType
    nonce:            uint64
    max_fees_per_gas: BasicFeesPerGas
    gas:              GasAmount
    to:               ExecutionAddress
    value:            uint256
    input_:           ProgressiveList

class RlpLegacyReplayableBasicTransaction(Container):
    payload:   RlpLegacyReplayableBasicTransactionPayload
    signature: Secp256k1ExecutionSignature

# Replayable CREATE
class RlpLegacyReplayableCreateTransactionPayload(
    ProgressiveContainer(active_fields=[1, 0, 1, 1, 1, 0, 1, 1])
):
    type_:            TransactionType
    nonce:            uint64
    max_fees_per_gas: BasicFeesPerGas
    gas:              GasAmount
    value:            uint256
    input_:           ProgressiveList

class RlpLegacyReplayableCreateTransaction(Container):
    payload:   RlpLegacyReplayableCreateTransactionPayload
    signature: Secp256k1ExecutionSignature

# EIP-155 BASIC
class RlpLegacyBasicTransactionPayload(
    ProgressiveContainer(active_fields=[1, 1, 1, 1, 1, 1, 1, 1])
):
    type_:            TransactionType
    chain_id:         ChainId
    nonce:            uint64
    max_fees_per_gas: BasicFeesPerGas
    gas:              GasAmount
    to:               ExecutionAddress
    value:            uint256
    input_:           ProgressiveList

class RlpLegacyBasicTransaction(Container):
    payload:   RlpLegacyBasicTransactionPayload
    signature: Secp256k1ExecutionSignature

# EIP-155 CREATE
class RlpLegacyCreateTransactionPayload(
    ProgressiveContainer(active_fields=[1, 1, 1, 1, 1, 0, 1, 1])
):
    type_:            TransactionType
    chain_id:         ChainId
    nonce:            uint64
    max_fees_per_gas: BasicFeesPerGas
    gas:              GasAmount
    value:            uint256
    input_:           ProgressiveList

class RlpLegacyCreateTransaction(Container):
    payload:   RlpLegacyCreateTransactionPayload
    signature: Secp256k1ExecutionSignature
