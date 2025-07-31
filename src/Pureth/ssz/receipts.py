from typing import Optional, List as PyList
from remerkleable.basic import boolean, uint64, Bytes32, Bytes20
from remerkleable.complex import (
    StableContainer, Profile, Container, List, ProgressiveBitlist, ProgressiveList
)
from remerkleable.union import CompatibleUnion

ExecutionAddress = Bytes20
GasAmount        = uint64
Hash32           = Bytes32

MAX_TOPICS_PER_LOG = 4

class Log(Container):
    address: ExecutionAddress
    topics:  List[Hash32, MAX_TOPICS_PER_LOG]
    data:    ProgressiveBitlist


class ReceiptContainer(StableContainer[6]):
    """
    Slot map
      0  from_
      1  gas_used
      2  contract_address
      3  logs
      4  status
      5  authorities
    """
    from_:            Optional[ExecutionAddress]
    gas_used:         Optional[GasAmount]
    contract_address: Optional[ExecutionAddress]
    logs:             Optional[ProgressiveList[Log]]
    status:           Optional[boolean]
    authorities:      Optional[ProgressiveList[ExecutionAddress]]

class BasicReceipt(Profile[ReceiptContainer]):
    from_:    ExecutionAddress
    gas_used: GasAmount
    logs:     ProgressiveList[Log]
    status:   boolean

class CreateReceipt(Profile[ReceiptContainer]):
    from_:            ExecutionAddress
    gas_used:         GasAmount
    contract_address: ExecutionAddress
    logs:             ProgressiveList[Log]
    status:           boolean

class SetCodeReceipt(Profile[ReceiptContainer]):
    from_:        ExecutionAddress
    gas_used:     GasAmount
    logs:         ProgressiveList[Log]
    status:       boolean
    authorities:  ProgressiveList[ExecutionAddress]

class Receipt(CompatibleUnion[
    BasicReceipt,
    CreateReceipt,
    SetCodeReceipt,
]):
    pass

def receipts_root(receipts: PyList[Receipt]) -> Hash32:
    return List[Receipt](receipts).hash_tree_root()
