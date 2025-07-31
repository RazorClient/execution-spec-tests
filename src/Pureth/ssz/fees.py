# ethereum_test_types/Pureth/ssz/fees.py
from remerkleable.complex import ProgressiveContainer
from .base import FeePerGas


class BasicFeesPerGas(ProgressiveContainer(active_fields=[1])):
    regular: FeePerGas


class BlobFeesPerGas(ProgressiveContainer(active_fields=[1, 1])):
    regular: FeePerGas
    blob:    FeePerGas
