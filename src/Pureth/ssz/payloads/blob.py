from remerkleable.complex import ProgressiveContainer, Container, ProgressiveList
from ..base import (TransactionType, ChainId, uint64, GasAmount, ExecutionAddress,uint256, VersionedHash)
from ..fees import BlobFeesPerGas, BasicFeesPerGas
from .access_list import AccessTuple
from ..signature import Secp256k1ExecutionSignature
    
# 0x03 BASIC (to present)
class RlpBlobTransactionPayload(
    ProgressiveContainer(active_fields=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
):
    type_:                     TransactionType    # 0x03
    chain_id:                  ChainId
    nonce:                     uint64
    max_fees_per_gas:          BlobFeesPerGas
    gas:                       GasAmount
    to:                        ExecutionAddress
    value:                     uint256
    input_:                    ProgressiveList
    access_list:               ProgressiveList[AccessTuple]
    max_priority_fees_per_gas: BasicFeesPerGas
    blob_versioned_hashes:     ProgressiveList[VersionedHash]


class RlpBlobTransaction(Container):
    payload:   RlpBlobTransactionPayload
    signature: Secp256k1ExecutionSignature

