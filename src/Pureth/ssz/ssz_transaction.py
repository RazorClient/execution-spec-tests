from remerkleable.union import Union
from ethereum_test_base_types import (
    Transaction as RlpTransaction,
    TransactionType,
    AccessList,
    Address,
    Bytes,
    CamelModel,
    Hash,
    HexNumber,
    NumberBoundTypeVar,
    TestAddress,
    TestPrivateKey,
)

from .signature import Secp256k1ExecutionSignature

from .payloads.legacy import (
    RlpLegacyReplayableBasicTransaction,
    RlpLegacyReplayableCreateTransaction,
    RlpLegacyBasicTransaction,
    RlpLegacyCreateTransaction,
)

from .payloads.access_list import (
    RlpAccessListBasicTransaction,
    RlpAccessListCreateTransaction,
)

from .payloads.fee_market import (
    RlpBasicTransaction        as RlpFeeMarketBasicTransaction,
    RlpCreateTransaction       as RlpFeeMarketCreateTransaction,
)

from .payloads.blob import (
    RlpBlobBasicTransaction,
    RlpBlobCreateTransaction,
)

from .payloads.set_code import RlpSetCodeTransaction

class RlpTransaction(
    Union[
        RlpLegacyReplayableBasicTransaction,
        RlpLegacyReplayableCreateTransaction,
        RlpLegacyBasicTransaction,
        RlpLegacyCreateTransaction,
        RlpAccessListBasicTransaction,
        RlpAccessListCreateTransaction,
        RlpFeeMarketBasicTransaction,
        RlpFeeMarketCreateTransaction,
        RlpBlobBasicTransaction,
        RlpBlobCreateTransaction,
        RlpSetCodeTransaction,
    ]
):
    pass

class TransactionSSZ(
    Union[
        RlpTransaction,
    ]
):
    pass

PAYLOAD_MAP: Dict[str, Tuple[type, type]] = {
    "legacy_replayable": (
        RlpLegacyReplayableBasicTransaction,
        RlpLegacyReplayableCreateTransaction,
    ),
    "legacy": (
        RlpLegacyBasicTransaction,
        RlpLegacyCreateTransaction,
    ),
    "access_list": (
        RlpAccessListBasicTransaction,
        RlpAccessListCreateTransaction,
    ),
    "fee_market": (
        RlpFeeMarketBasicTransaction,
        RlpFeeMarketCreateTransaction,
    ),
    "blob": (
        RlpBlobBasicTransaction,
        RlpBlobCreateTransaction,
    ),
    "set_code": (
        RlpSetCodeTransaction,
        RlpSetCodeTransaction,
    ),
}


def make_signed_tx(
    *, tx_type: str, secret_key: bytes, **tx_fields
) -> Tuple[TransactionSSZ, Secp256k1ExecutionSignature]:
    try:
        basic_cls, create_cls = PAYLOAD_MAP[tx_type]
    except KeyError as exc:
        raise ValueError(f"unsupported tx_type: {tx_type}") from exc

    payload_cls = basic_cls if tx_fields.get("to") not in (None, b"") else create_cls
    payload = payload_cls(**tx_fields)
    tx = TransactionSSZ.create(RlpTransaction.create(payload))

    digest = tx.hash_tree_root().to_bytes()
    sig_bytes = PrivateKey(secret_key).sign_recoverable(digest, hasher=None)
    r = int.from_bytes(sig_bytes[0:32], "big")
    s = int.from_bytes(sig_bytes[32:64], "big")
    y_parity = sig_bytes[64]
    signature = Secp256k1ExecutionSignature(
        secp256k1=secp256k1_pack(r, s, y_parity)
    )
    return tx, signature

class SignedTransaction(BaseModel):
    """Pydantic wrapper that builds and signs an SSZ transaction."""

    tx_type: str
    secret_key: bytes
    tx: TransactionSSZ | None = Field(default=None, exclude=True)
    signature: Secp256k1ExecutionSignature | None = Field(default=None, exclude=True)

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True, validate_assignment=True
    )

    def model_post_init(self, __context: Any) -> None:
        """Construct the SSZ transaction and signature from provided fields."""
        super().model_post_init(__context)
        tx_fields = self.model_dump(
            exclude={"tx_type", "secret_key", "tx", "signature"},
            exclude_none=True,
        )
        self.tx, self.signature = make_signed_tx(
            tx_type=self.tx_type, secret_key=self.secret_key, **tx_fields
        )
