"""Rezolvă valoarea index din serviciu HA sau input_number."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError


DEFAULT_INPUT_ENTITY = "input_number.index_gaz_premier"


def resolve_index_from_call(
    hass: HomeAssistant,
    call: ServiceCall,
    *,
    input_entity: str = DEFAULT_INPUT_ENTITY,
) -> int:
    raw = call.data.get("index")
    if raw is not None and int(raw) > 0:
        return int(raw)

    state = hass.states.get(input_entity)
    if state and state.state not in ("unknown", "unavailable", "", None):
        try:
            value = int(float(state.state))
            if value > 0:
                return value
        except (TypeError, ValueError) as exc:
            raise ServiceValidationError(
                f"Valoare invalidă în {input_entity}: {state.state}"
            ) from exc

    raise ServiceValidationError(
        f"Index lipsă — completează {input_entity} sau trimite /indexgaze <valoare>"
    )
