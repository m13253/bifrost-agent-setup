import dataclasses
import decimal

import dacite
import dacite.data

from . import utils


@dataclasses.dataclass
class FallbackMetadata:
    context_length: int = 262144
    max_output_tokens: int = 65536


@dataclasses.dataclass
class Config:
    bifrost_name: str
    bifrost_url: str
    virtual_key: str | None
    fallback_metadata: FallbackMetadata = dataclasses.field(
        default_factory=FallbackMetadata
    )


@dataclasses.dataclass
class Models:
    data: list[Model] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Architecture:
    input_modalities: list[str] | None = None
    output_modalities: list[str] | None = None


@dataclasses.dataclass
class Pricing:
    prompt: str | None = None
    completion: str | None = None
    input_cache_read: str | None = None
    input_cache_write: str | None = None


@dataclasses.dataclass
class TopProvider:
    context_length: int | None = None
    max_completion_tokens: int | None = None


@dataclasses.dataclass
class PerRequestLimits:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


@dataclasses.dataclass
class Reasoning:
    mandatory: bool | None = None
    supported_efforts: list[str] | None = None
    default_effort: str | None = None


@dataclasses.dataclass
class Model:
    id: str
    name: str | None = None
    normalized_name: str | None = None
    context_length: int | None = None
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    architecture: Architecture = dataclasses.field(default_factory=Architecture)
    pricing: Pricing | None = None
    top_provider: TopProvider = dataclasses.field(default_factory=TopProvider)
    per_request_limits: PerRequestLimits = dataclasses.field(
        default_factory=PerRequestLimits
    )
    reasoning: Reasoning | None = None


def from_dict_cast_int[T](data_class: type[T], data: dacite.data.Data) -> T:
    return dacite.from_dict(
        data_class,
        data,
        dacite.Config(type_hooks={decimal.Decimal: utils.decimal_as_int_exact}),
    )
