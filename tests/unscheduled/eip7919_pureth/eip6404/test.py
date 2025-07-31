import pytest
from ethereum_test_types.transaction_types import Transaction as RlpTx, AuthorizationTuple
from ethereum_test_base_types import Address, Bytes, Hash, AccessList, TestPrivateKey
from Pureth.ssz.rlpbridge import rlp_to_ssz, ssz_to_rlp
from Pureth.ssz.fees import BasicFeesPerGas, BlobFeesPerGas
from Pureth.ssz.payloads.legacy import RlpLegacyBasicTransactionPayload, RlpLegacyBasicTransaction
from Pureth.ssz.payloads.access_list import (
    AccessTuple as SszAccessTuple,
    RlpAccessListBasicTransactionPayload,
    RlpAccessListBasicTransaction,
)
from Pureth.ssz.payloads.fee_market import (
    RlpBasicTransactionPayload as RlpFeeMarketBasicTransactionPayload,
    RlpBasicTransaction as RlpFeeMarketBasicTransaction,
)
from Pureth.ssz.payloads.blob import RlpBlobBasicTransactionPayload, RlpBlobBasicTransaction
from Pureth.ssz.payloads.set_code import (
    RlpSetCodeTransactionPayload,
    RlpSetCodeTransaction,
    RlpAuthorization,
    RlpBasicAuthorizationPayload,
)
from Pureth.ssz.base import ProgressiveList, Hash32, VersionedHash
from Pureth.ssz.signature import Secp256k1ExecutionSignature, secp256k1_pack

def test_legacy_basic_roundtrip():
    tx = RlpTx(
        ty=0,
        chain_id=1,
        nonce=1,
        gas_price=1,
        gas_limit=21000,
        to=Address(0x1111111111111111111111111111111111111111),
        value=1,
        data=Bytes(b"\x01\x02"),
    )
    tx.sign()

    ssz_tx = rlp_to_ssz(tx)

    expected_payload = RlpLegacyBasicTransactionPayload(
        type_=0,
        chain_id=1,
        nonce=1,
        max_fees_per_gas=BasicFeesPerGas(regular=1),
        gas=21000,
        to=bytes(tx.to),
        value=1,
        input_=_bytes_to_pbl(bytes(tx.data)),
    )
    expected = RlpLegacyBasicTransaction(payload=expected_payload, signature=_pack_signature(tx))

    assert ssz_tx.value == expected

    roundtrip = ssz_to_rlp(ssz_tx)
    assert tx.rlp() == roundtrip.rlp()


def test_access_list_roundtrip():
    alist = [
        AccessList(
            address=Address(0x2222222222222222222222222222222222222222),
            storage_keys=[Hash(0x01.to_bytes(32, "big"))],
        )
    ]
    tx = RlpTx(
        ty=1,
        chain_id=1,
        nonce=2,
        gas_price=1,
        gas_limit=50000,
        to=Address(0x3333333333333333333333333333333333333333),
        value=5,
        data=Bytes(b""),
        access_list=alist,
    )
    tx.sign()

    ssz_tx = rlp_to_ssz(tx)

    expected_payload = RlpAccessListBasicTransactionPayload(
        type_=1,
        chain_id=1,
        nonce=2,
        max_fees_per_gas=BasicFeesPerGas(regular=1),
        gas=50000,
        to=bytes(tx.to),
        value=5,
        input_=_bytes_to_pbl(b""),
        access_list=_alist_to_ssz(alist),
    )
    expected = RlpAccessListBasicTransaction(payload=expected_payload, signature=_pack_signature(tx))

    assert ssz_tx.value == expected

    roundtrip = ssz_to_rlp(ssz_tx)
    assert tx.rlp() == roundtrip.rlp()


def test_fee_market_roundtrip():
    tx = RlpTx(
        ty=2,
        chain_id=1,
        nonce=3,
        max_fee_per_gas=7,
        max_priority_fee_per_gas=1,
        gas_limit=21000,
        to=Address(0x4444444444444444444444444444444444444444),
        value=0,
        data=Bytes(b""),
        access_list=[],
    )
    tx.sign()

    ssz_tx = rlp_to_ssz(tx)

    expected_payload = RlpFeeMarketBasicTransactionPayload(
        type_=2,
        chain_id=1,
        nonce=3,
        max_fees_per_gas=BasicFeesPerGas(regular=7),
        gas=21000,
        to=bytes(tx.to),
        value=0,
        input_=_bytes_to_pbl(b""),
        access_list=ProgressiveList[SszAccessTuple]([]),
        max_priority_fees_per_gas=BasicFeesPerGas(regular=1),
    )
    expected = RlpFeeMarketBasicTransaction(payload=expected_payload, signature=_pack_signature(tx))

    assert ssz_tx.value == expected

    roundtrip = ssz_to_rlp(ssz_tx)
    assert tx.rlp() == roundtrip.rlp()


def test_blob_roundtrip():
    bv_hash = Hash(b"\x12" * 32)
    tx = RlpTx(
        ty=3,
        chain_id=1,
        nonce=4,
        max_fee_per_gas=7,
        max_priority_fee_per_gas=1,
        max_fee_per_blob_gas=3,
        gas_limit=50000,
        to=Address(0x5555555555555555555555555555555555555555),
        value=0,
        data=Bytes(b""),
        access_list=[],
        blob_versioned_hashes=[bv_hash],
    )
    tx.sign()

    ssz_tx = rlp_to_ssz(tx)

    expected_payload = RlpBlobBasicTransactionPayload(
        type_=3,
        chain_id=1,
        nonce=4,
        max_fees_per_gas=BlobFeesPerGas(regular=7, blob=3),
        gas=50000,
        to=bytes(tx.to),
        value=0,
        input_=_bytes_to_pbl(b""),
        access_list=ProgressiveList[SszAccessTuple]([]),
        max_priority_fees_per_gas=BasicFeesPerGas(regular=1),
        blob_versioned_hashes=_blob_hashes_to_ssz([bv_hash]),
    )
    expected = RlpBlobBasicTransaction(payload=expected_payload, signature=_pack_signature(tx))

    assert ssz_tx.value == expected

    roundtrip = ssz_to_rlp(ssz_tx)
    assert tx.rlp() == roundtrip.rlp()


def test_set_code_roundtrip():
    auth = AuthorizationTuple(
        address=Address(0x6666666666666666666666666666666666666666),
        nonce=0,
        secret_key=Hash(TestPrivateKey),
    )
    tx = RlpTx(
        ty=4,
        chain_id=1,
        nonce=5,
        max_fee_per_gas=7,
        max_priority_fee_per_gas=1,
        gas_limit=60000,
        to=Address(0x7777777777777777777777777777777777777777),
        value=0,
        data=Bytes(b""),
        access_list=[],
        authorization_list=[auth],
    )
    tx.sign()

    ssz_tx = rlp_to_ssz(tx)

    expected_payload = RlpSetCodeTransactionPayload(
        type_=4,
        chain_id=1,
        nonce=5,
        max_fees_per_gas=BasicFeesPerGas(regular=7),
        gas=60000,
        to=bytes(tx.to),
        value=0,
        input_=_bytes_to_pbl(b""),
        access_list=ProgressiveList[SszAccessTuple]([]),
        max_priority_fees_per_gas=BasicFeesPerGas(regular=1),
        authorization_list=_auth_list_to_ssz([auth], chain_id=1),
    )
    expected = RlpSetCodeTransaction(payload=expected_payload, signature=_pack_signature(tx))

    assert ssz_tx.value == expected

    roundtrip = ssz_to_rlp(ssz_tx)
    assert tx.rlp() == roundtrip.rlp()