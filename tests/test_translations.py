"""UI translations."""

from __future__ import annotations

import json
import re
from pathlib import Path

TRANSLATIONS = Path(__file__).parent.parent / "custom_components" / "euribor_rates" / "translations"


def flatten(tree: dict, prefix: str = "") -> dict[str, str]:
    result = {}
    for key, value in tree.items():
        if isinstance(value, dict):
            result |= flatten(value, f"{prefix}{key}.")
        else:
            result[f"{prefix}{key}"] = value
    return result


def test_finnish_has_the_same_texts_and_placeholders_as_english() -> None:
    english = flatten(json.loads((TRANSLATIONS / "en.json").read_text(encoding="utf-8")))
    finnish = flatten(json.loads((TRANSLATIONS / "fi.json").read_text(encoding="utf-8")))
    assert finnish.keys() == english.keys()
    for key, text in english.items():
        assert re.findall(r"\{\w+\}", finnish[key]) == re.findall(r"\{\w+\}", text), key


def test_every_maturity_has_a_device_name_in_both_languages() -> None:
    from custom_components.euribor_rates.const import MATURITIES

    for language in ("en", "fi"):
        devices = json.loads((TRANSLATIONS / f"{language}.json").read_text(encoding="utf-8"))["device"]
        assert set(devices) == {f"maturity_{maturity.replace(' ', '_')}" for maturity in MATURITIES}, language
