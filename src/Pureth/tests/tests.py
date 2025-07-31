from ethereum_test_tools import keccak256
from Pureth.ssz.ssz_transaction import (
    make_signed_tx,
    secp256k1_recover_signer,
    secp256k1_validate,
)


def test_make_signed_tx_and_recover():
    secret_key = bytes.fromhex("1".zfill(64))
    tx, signature = make_signed_tx(
        tx_type="legacy",
        secret_key=secret_key,
        nonce=0,
        gas_price=1,
        gas_limit=21_000,
        to=b"\xaa" * 20,
        value=0,
        data=b"",
    )

    # Signature should be well-formed
    secp256k1_validate(signature.secp256k1)

    # Recover signer and compare with expected address
    signer = secp256k1_recover_signer(
        signature.secp256k1, tx.hash_tree_root().to_bytes()
    )
    expected = keccak256(
        PrivateKey(secret_key).public_key.format(compressed=False)[1:]
    )[12:]
    assert signer == expected