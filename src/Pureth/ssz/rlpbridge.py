"""
RLP → SSZ bridge
================
Convert a `transaction_types.Transaction` (RLP era) into the normalised
SSZ transaction union defined under `ethereum_test_types.Pureth.ssz`.

>>> from ethereum_test_types.transaction_types import Transaction as RlpTx
>>> from ethereum_test_types.Pureth.ssz.bridge import rlp_to_ssz
>>> ssz_tx = rlp_to_ssz(rlp_tx)          # returns an SSZ `Transaction`
>>> ssz_bytes = ssz_tx.serialize()       # use in Engine-API payloads
"""

from typing import List as _List

from ethereum_test_types.transaction_types import (
    AuthorizationTuple,
    Transaction as RlpTx,
)
from ethereum_test_base_types import (
    AccessList as RlpAccessList,
    Address,
    Bytes,
    Hash,
)

from remerkleable.complex import ProgressiveList, List
from remerkleable.basic import uint8

from .transaction import Transaction as SszTx  # the top-level union
from .payloads.legacy import (
    RlpLegacyReplayableBasicTransaction, RlpLegacyReplayableBasicTransactionPayload,
    RlpLegacyReplayableCreateTransaction, RlpLegacyReplayableCreateTransactionPayload,
    RlpLegacyBasicTransaction, RlpLegacyBasicTransactionPayload,
    RlpLegacyCreateTransaction, RlpLegacyCreateTransactionPayload,
)
from .payloads.access_list import (
    AccessTuple,
    RlpAccessListBasicTransaction,  RlpAccessListBasicTransactionPayload,
    RlpAccessListCreateTransaction, RlpAccessListCreateTransactionPayload,
)
from .payloads.fee_market import (
    RlpBasicTransaction              as RlpFeeMarketBasicTransaction,
    RlpBasicTransactionPayload       as RlpFeeMarketBasicTransactionPayload,
    RlpCreateTransaction             as RlpFeeMarketCreateTransaction,
    RlpCreateTransactionPayload      as RlpFeeMarketCreateTransactionPayload,
)
from .payloads.blob import (
    RlpBlobBasicTransaction,  RlpBlobBasicTransactionPayload,
    RlpBlobCreateTransaction, RlpBlobCreateTransactionPayload,
)
from .payloads.set_code import (
    RlpAuthorization,
    RlpReplayableBasicAuthorizationPayload, RlpBasicAuthorizationPayload,
    RlpSetCodeTransaction, RlpSetCodeTransactionPayload,
)
from .fees import BasicFeesPerGas, BlobFeesPerGas
from .signature import (
    Secp256k1ExecutionSignature,
    secp256k1_pack,
    secp256k1_unpack,
)
from .base import VersionedHash, ExecutionAddress, ProgressiveList, Hash32

def _pack_sig(tx: RlpTx) -> Secp256k1ExecutionSignature:
    """Convert (v,r,s) into the 65-byte secp256k1 blob."""
    return Secp256k1ExecutionSignature(
        secp256k1=secp256k1_pack(int(tx.r), int(tx.s), int(tx.v % 2))
    )

def _py_bytes_to_pbl(data: bytes) -> ProgressiveList:
    return ProgressiveList(data)

def _to_access_list(al: _List[RlpAccessList] | None) -> ProgressiveList[AccessTuple]:
    if not al:
        return ProgressiveList[AccessTuple]()
    tuples: _List[AccessTuple] = []
    for t in al:
        tuples.append(
            AccessTuple(
                address=bytes(t.address),
                storage_keys=ProgressiveList[Hash32]([bytes(k) for k in t.storage_keys]),
            )
        )
    return ProgressiveList[AccessTuple](tuples)

def _to_blob_hashes(bvhs: _List[bytes] | None) -> ProgressiveList[VersionedHash]:
    if not bvhs:
        return ProgressiveList[VersionedHash]()
    return ProgressiveList[VersionedHash]([bytes(h) for h in bvhs])

# reverse direction helpers (ssz->rlp)
def _unpack_sig(sig: Secp256k1ExecutionSignature) -> tuple[int, int, int]:
    """Split the packed 65-byte signature into (r, s, y_parity)."""
    return secp256k1_unpack(bytes(sig.secp256k1))


def _pbl_to_py_bytes(pbl: ProgressiveList) -> bytes:
    """Convert a ProgressiveList of bytes back to a Python `bytes` object."""
    return bytes(pbl)


def _from_access_list(alist: ProgressiveList[AccessTuple] | None) -> _List[RlpAccessList]:
    """Map an SSZ access list into the RLP representation."""
    if not alist:
        return []
    result: _List[RlpAccessList] = []
    for t in alist:
        result.append(
            RlpAccessList(
                address=Address(bytes(t.address)),
                storage_keys=[Hash(bytes(k)) for k in t.storage_keys],
            )
        )
    return result


def _from_blob_hashes(hashes: ProgressiveList[VersionedHash] | None) -> _List[bytes]:
    if not hashes:
        return []
    return [bytes(h) for h in hashes]


def _from_auth_list(
    auths: ProgressiveList[RlpAuthorization] | None,
    chain_id: int | None,
) -> _List[AuthorizationTuple]:
    if not auths:
        return []
    result: _List[AuthorizationTuple] = []
    for auth in auths:
        payload = auth.value
        if isinstance(payload, RlpReplayableBasicAuthorizationPayload):
            result.append(
                AuthorizationTuple(
                    chain_id=None,
                    address=Address(bytes(payload.address)),
                    nonce=int(payload.nonce),
                )
            )
        else:  # RlpBasicAuthorizationPayload
            result.append(
                AuthorizationTuple(
                    chain_id=int(payload.chain_id),
                    address=Address(bytes(payload.address)),
                    nonce=int(payload.nonce),
                )
            )
    return result

def rlp_to_ssz(tx: RlpTx) -> SszTx:
    """
    Map an RLP Transaction instance to its SSZ union counterpart.
    Raises `NotImplementedError` for unknown types.
    """
    ty = tx.ty
    sig = _pack_sig(tx)

    # YPE 0x00
    if ty == 0:
        fee = BasicFeesPerGas(regular=int(tx.gas_price))
        if tx.chain_id is None:   
            if tx.to is not None:
                payload = RlpLegacyReplayableBasicTransactionPayload(
                    type_=0, nonce=int(tx.nonce), max_fees_per_gas=fee,
                    gas=int(tx.gas_limit), to=bytes(tx.to),
                    value=int(tx.value), input_=_py_bytes_to_pbl(bytes(tx.data)),
                )
                return SszTx(RlpLegacyReplayableBasicTransaction(payload=payload, signature=sig))
            else:  # CREATE
                payload = RlpLegacyReplayableCreateTransactionPayload(
                    type_=0, nonce=int(tx.nonce), max_fees_per_gas=fee,
                    gas=int(tx.gas_limit), value=int(tx.value),
                    input_=_py_bytes_to_pbl(bytes(tx.data)),
                )
                return SszTx(RlpLegacyReplayableCreateTransaction(payload=payload, signature=sig))
        else:                      
            if tx.to is not None:
                payload = RlpLegacyBasicTransactionPayload(
                    type_=0, chain_id=int(tx.chain_id), nonce=int(tx.nonce),
                    max_fees_per_gas=fee, gas=int(tx.gas_limit), to=bytes(tx.to),
                    value=int(tx.value), input_=_py_bytes_to_pbl(bytes(tx.data)),
                )
                return SszTx(RlpLegacyBasicTransaction(payload=payload, signature=sig))
            else:
                payload = RlpLegacyCreateTransactionPayload(
                    type_=0, chain_id=int(tx.chain_id), nonce=int(tx.nonce),
                    max_fees_per_gas=fee, gas=int(tx.gas_limit),
                    value=int(tx.value), input_=_py_bytes_to_pbl(bytes(tx.data)),
                )
                return SszTx(RlpLegacyCreateTransaction(payload=payload, signature=sig))

    # (EIP-2930)
    if ty == 1:
        fee   = BasicFeesPerGas(regular=int(tx.max_fee_per_gas))
        alist = _to_access_list(tx.access_list)
        if tx.to is not None:
            payload = RlpAccessListBasicTransactionPayload(
                type_=1, chain_id=int(tx.chain_id), nonce=int(tx.nonce),
                max_fees_per_gas=fee, gas=int(tx.gas_limit), to=bytes(tx.to),
                value=int(tx.value), input_=_py_bytes_to_pbl(bytes(tx.data)),
                access_list=alist,
            )
            return SszTx(RlpAccessListBasicTransaction(payload=payload, signature=sig))
        else:
            payload = RlpAccessListCreateTransactionPayload(
                type_=1, chain_id=int(tx.chain_id), nonce=int(tx.nonce),
                max_fees_per_gas=fee, gas=int(tx.gas_limit),
                value=int(tx.value), input_=_py_bytes_to_pbl(bytes(tx.data)),
                access_list=alist,
            )
            return SszTx(RlpAccessListCreateTransaction(payload=payload, signature=sig))

    # (EIP-1559)
    if ty == 2:
        fee        = BasicFeesPerGas(regular=int(tx.max_fee_per_gas))
        alist      = _to_access_list(tx.access_list)
        max_pri_fee = BasicFeesPerGas(regular=int(tx.max_priority_fee_per_gas))
        if tx.to is not None:
            payload = RlpFeeMarketBasicTransactionPayload(
                type_=2, chain_id=int(tx.chain_id), nonce=int(tx.nonce),
                max_fees_per_gas=fee, gas=int(tx.gas_limit), to=bytes(tx.to),
                value=int(tx.value), input_=_py_bytes_to_pbl(bytes(tx.data)),
                access_list=alist, max_priority_fees_per_gas=max_pri_fee,
            )
            return SszTx(RlpFeeMarketBasicTransaction(payload=payload, signature=sig))
        else:
            payload = RlpFeeMarketCreateTransactionPayload(
                type_=2, chain_id=int(tx.chain_id), nonce=int(tx.nonce),
                max_fees_per_gas=fee, gas=int(tx.gas_limit),
                value=int(tx.value), input_=_py_bytes_to_pbl(bytes(tx.data)),
                access_list=alist, max_priority_fees_per_gas=max_pri_fee,
            )
            return SszTx(RlpFeeMarketCreateTransaction(payload=payload, signature=sig))

    # (EIP-4844 Blob)
    if ty == 3:
        fee        = BlobFeesPerGas(
            regular=int(tx.max_fee_per_gas),
            blob   =int(tx.max_fee_per_blob_gas),
        )
        alist      = _to_access_list(tx.access_list)
        max_pri_fee = BasicFeesPerGas(regular=int(tx.max_priority_fee_per_gas))
        bv_hashes  = _to_blob_hashes(tx.blob_versioned_hashes)
        if tx.to is not None:
            payload = RlpBlobBasicTransactionPayload(
                type_=3, chain_id=int(tx.chain_id), nonce=int(tx.nonce),
                max_fees_per_gas=fee, gas=int(tx.gas_limit), to=bytes(tx.to),
                value=int(tx.value), input_=_py_bytes_to_pbl(bytes(tx.data)),
                access_list=alist, max_priority_fees_per_gas=max_pri_fee,
                blob_versioned_hashes=bv_hashes,
            )
            return SszTx(RlpBlobBasicTransaction(payload=payload, signature=sig))
        else:
            payload = RlpBlobCreateTransactionPayload(
                type_=3, chain_id=int(tx.chain_id), nonce=int(tx.nonce),
                max_fees_per_gas=fee, gas=int(tx.gas_limit),
                value=int(tx.value), input_=_py_bytes_to_pbl(bytes(tx.data)),
                access_list=alist, max_priority_fees_per_gas=max_pri_fee,
                blob_versioned_hashes=bv_hashes,
            )
            return SszTx(RlpBlobCreateTransaction(payload=payload, signature=sig))

    # (EIP-7702 Set-Code)
    if ty == 4:
        fee        = BasicFeesPerGas(regular=int(tx.max_fee_per_gas))
        alist      = _to_access_list(tx.access_list)
        max_pri_fee = BasicFeesPerGas(regular=int(tx.max_priority_fee_per_gas))

        auth_ssz: _List[RlpAuthorization] = []
        for auth in (tx.authorization_list or []):
            if tx.chain_id is None:
                # replayable
                a = RlpReplayableBasicAuthorizationPayload(
                    magic=5, address=bytes(auth.address), nonce=int(auth.nonce)
                )
            else:
                a = RlpBasicAuthorizationPayload(
                    magic=5, chain_id=int(tx.chain_id),
                    address=bytes(auth.address), nonce=int(auth.nonce)
                )
            auth_ssz.append(a)

        payload = RlpSetCodeTransactionPayload(
            type_=4, chain_id=int(tx.chain_id), nonce=int(tx.nonce),
            max_fees_per_gas=fee, gas=int(tx.gas_limit), to=bytes(tx.to),
            value=int(tx.value), input_=_py_bytes_to_pbl(bytes(tx.data)),
            access_list=alist, max_priority_fees_per_gas=max_pri_fee,
            authorization_list=ProgressiveList[RlpAuthorization](auth_ssz),
        )
        return SszTx(RlpSetCodeTransaction(payload=payload, signature=sig))
    raise NotImplementedError(f"Unsupported tx.type {ty}")

def ssz_to_rlp(tx: SszTx) -> RlpTx:
    """Map an SSZ Transaction union back to the RLP-era Transaction model."""
    v = tx.value

    # Legacy 0x00 replayable basic
    if isinstance(v, RlpLegacyReplayableBasicTransaction):
        payload = v.payload
        r, s, y = _unpack_sig(v.signature)
        return RlpTx(
            ty=0,
            chain_id=None,
            nonce=int(payload.nonce),
            gas_price=int(payload.max_fees_per_gas.regular),
            gas_limit=int(payload.gas),
            to=Address(bytes(payload.to)),
            value=int(payload.value),
            data=Bytes(_pbl_to_py_bytes(payload.input_)),
            v=y + 27,
            r=r,
            s=s,
        )

    if isinstance(v, RlpLegacyReplayableCreateTransaction):
        payload = v.payload
        r, s, y = _unpack_sig(v.signature)
        return RlpTx(
            ty=0,
            chain_id=None,
            nonce=int(payload.nonce),
            gas_price=int(payload.max_fees_per_gas.regular),
            gas_limit=int(payload.gas),
            to=None,
            value=int(payload.value),
            data=Bytes(_pbl_to_py_bytes(payload.input_)),
            v=y + 27,
            r=r,
            s=s,
        )

    if isinstance(v, RlpLegacyBasicTransaction):
        payload = v.payload
        r, s, y = _unpack_sig(v.signature)
        cid = int(payload.chain_id)
        return RlpTx(
            ty=0,
            chain_id=cid,
            nonce=int(payload.nonce),
            gas_price=int(payload.max_fees_per_gas.regular),
            gas_limit=int(payload.gas),
            to=Address(bytes(payload.to)),
            value=int(payload.value),
            data=Bytes(_pbl_to_py_bytes(payload.input_)),
            v=y + 35 + 2 * cid,
            r=r,
            s=s,
        )

    if isinstance(v, RlpLegacyCreateTransaction):
        payload = v.payload
        r, s, y = _unpack_sig(v.signature)
        cid = int(payload.chain_id)
        return RlpTx(
            ty=0,
            chain_id=cid,
            nonce=int(payload.nonce),
            gas_price=int(payload.max_fees_per_gas.regular),
            gas_limit=int(payload.gas),
            to=None,
            value=int(payload.value),
            data=Bytes(_pbl_to_py_bytes(payload.input_)),
            v=y + 35 + 2 * cid,
            r=r,
            s=s,
        )

    if isinstance(v, RlpAccessListBasicTransaction):
        payload = v.payload
        r, s, y = _unpack_sig(v.signature)
        return RlpTx(
            ty=1,
            chain_id=int(payload.chain_id),
            nonce=int(payload.nonce),
            gas_price=int(payload.max_fees_per_gas.regular),
            gas_limit=int(payload.gas),
            to=Address(bytes(payload.to)),
            value=int(payload.value),
            data=Bytes(_pbl_to_py_bytes(payload.input_)),
            access_list=_from_access_list(payload.access_list),
            v=y,
            r=r,
            s=s,
        )

    if isinstance(v, RlpAccessListCreateTransaction):
        payload = v.payload
        r, s, y = _unpack_sig(v.signature)
        return RlpTx(
            ty=1,
            chain_id=int(payload.chain_id),
            nonce=int(payload.nonce),
            gas_price=int(payload.max_fees_per_gas.regular),
            gas_limit=int(payload.gas),
            to=None,
            value=int(payload.value),
            data=Bytes(_pbl_to_py_bytes(payload.input_)),
            access_list=_from_access_list(payload.access_list),
            v=y,
            r=r,
            s=s,
        )

    if isinstance(v, RlpFeeMarketBasicTransaction):
        payload = v.payload
        r, s, y = _unpack_sig(v.signature)
        return RlpTx(
            ty=2,
            chain_id=int(payload.chain_id),
            nonce=int(payload.nonce),
            max_fee_per_gas=int(payload.max_fees_per_gas.regular),
            gas_limit=int(payload.gas),
            to=Address(bytes(payload.to)),
            value=int(payload.value),
            data=Bytes(_pbl_to_py_bytes(payload.input_)),
            access_list=_from_access_list(payload.access_list),
            max_priority_fee_per_gas=int(payload.max_priority_fees_per_gas.regular),
            v=y,
            r=r,
            s=s,
        )

    if isinstance(v, RlpFeeMarketCreateTransaction):
        payload = v.payload
        r, s, y = _unpack_sig(v.signature)
        return RlpTx(
            ty=2,
            chain_id=int(payload.chain_id),
            nonce=int(payload.nonce),
            max_fee_per_gas=int(payload.max_fees_per_gas.regular),
            gas_limit=int(payload.gas),
            to=None,
            value=int(payload.value),
            data=Bytes(_pbl_to_py_bytes(payload.input_)),
            access_list=_from_access_list(payload.access_list),
            max_priority_fee_per_gas=int(payload.max_priority_fees_per_gas.regular),
            v=y,
            r=r,
            s=s,
        )

    if isinstance(v, RlpBlobBasicTransaction):
        payload = v.payload
        r, s, y = _unpack_sig(v.signature)
        return RlpTx(
            ty=3,
            chain_id=int(payload.chain_id),
            nonce=int(payload.nonce),
            max_fee_per_gas=int(payload.max_fees_per_gas.regular),
            max_fee_per_blob_gas=int(payload.max_fees_per_gas.blob),
            gas_limit=int(payload.gas),
            to=Address(bytes(payload.to)),
            value=int(payload.value),
            data=Bytes(_pbl_to_py_bytes(payload.input_)),
            access_list=_from_access_list(payload.access_list),
            max_priority_fee_per_gas=int(payload.max_priority_fees_per_gas.regular),
            blob_versioned_hashes=_from_blob_hashes(payload.blob_versioned_hashes),
            v=y,
            r=r,
            s=s,
        )

    if isinstance(v, RlpBlobCreateTransaction):
        payload = v.payload
        r, s, y = _unpack_sig(v.signature)
        return RlpTx(
            ty=3,
            chain_id=int(payload.chain_id),
            nonce=int(payload.nonce),
            max_fee_per_gas=int(payload.max_fees_per_gas.regular),
            max_fee_per_blob_gas=int(payload.max_fees_per_gas.blob),
            gas_limit=int(payload.gas),
            to=None,
            value=int(payload.value),
            data=Bytes(_pbl_to_py_bytes(payload.input_)),
            access_list=_from_access_list(payload.access_list),
            max_priority_fee_per_gas=int(payload.max_priority_fees_per_gas.regular),
            blob_versioned_hashes=_from_blob_hashes(payload.blob_versioned_hashes),
            v=y,
            r=r,
            s=s,
        )

    if isinstance(v, RlpSetCodeTransaction):
        payload = v.payload
        r, s, y = _unpack_sig(v.signature)
        cid = int(payload.chain_id)
        return RlpTx(
            ty=4,
            chain_id=cid,
            nonce=int(payload.nonce),
            max_fee_per_gas=int(payload.max_fees_per_gas.regular),
            gas_limit=int(payload.gas),
            to=Address(bytes(payload.to)),
            value=int(payload.value),
            data=Bytes(_pbl_to_py_bytes(payload.input_)),
            access_list=_from_access_list(payload.access_list),
            max_priority_fee_per_gas=int(payload.max_priority_fees_per_gas.regular),
            authorization_list=_from_auth_list(payload.authorization_list, cid),
            v=y,
            r=r,
            s=s,
        )

    raise NotImplementedError("Unsupported SSZ transaction variant")
