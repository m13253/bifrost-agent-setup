import dataclasses

from . import schema


def model_supports_chat(model: schema.Model) -> bool:
    # Since model datasheet may be incomplete, we assume models support chat unless marked otherwise.
    return model.architecture is None or (
        (
            model.architecture.input_modalities is None
            or "text" in model.architecture.input_modalities
        )
        and (
            model.architecture.output_modalities is None
            or "text" in model.architecture.output_modalities
        )
    )


def model_supports_vision(model: schema.Model) -> bool:
    return (
        model.architecture is not None
        and model.architecture.input_modalities is not None
        and "image" in model.architecture.input_modalities
    )


@dataclasses.dataclass
class ModelContextLimits:
    context_length: int | None
    max_output_tokens: int | None

    @staticmethod
    def guess(model: schema.Model) -> ModelContextLimits:
        if model.max_output_tokens is None:
            max_output_tokens = model.per_request_limits.completion_tokens
        elif model.per_request_limits.completion_tokens is None:
            max_output_tokens = model.max_output_tokens
        else:
            max_output_tokens = min(
                model.max_output_tokens, model.per_request_limits.completion_tokens
            )

        if model.context_length is not None:
            context_length = model.context_length
        elif model.max_input_tokens is not None and max_output_tokens is not None:
            context_length = model.max_input_tokens + max_output_tokens
        else:
            context_length = None

        if context_length is None:
            context_length = model.top_provider.context_length
        elif model.top_provider.context_length is not None:
            context_length = min(context_length, model.top_provider.context_length)

        if max_output_tokens is None:
            max_output_tokens = model.top_provider.max_completion_tokens
        elif model.top_provider.max_completion_tokens is not None:
            max_output_tokens = min(
                max_output_tokens, model.top_provider.max_completion_tokens
            )

        return ModelContextLimits(
            context_length=context_length,
            max_output_tokens=max_output_tokens,
        )
