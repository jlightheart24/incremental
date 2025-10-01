"""Simple synthesis recipe definitions."""

from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass(frozen=True)
class SynthesisRecipe:
    recipe_id: str
    name: str
    materials: Dict[str, int]
    output_item_id: str
    description: str = ""


SYNTHESIS_RECIPES: Dict[str, SynthesisRecipe] = {
    "bandana_upgrade": SynthesisRecipe(
        recipe_id="bandana_upgrade",
        name="Warded Bandana",
        materials={
            "dark_shard": 2,
            "bright_shard": 1,
        },
        output_item_id="elven_bandana",
        description="Imbue a bandana with protective light.",
    ),
    "champion_belt": SynthesisRecipe(
        recipe_id="champion_belt",
        name="Champion Belt",
        materials={
            "dark_shard": 1,
            "mythril_fragment": 2,
        },
        output_item_id="champion_belt",
        description="Forge a defensive belt from rare ore.",
    ),
}


def iter_recipes() -> Iterable[SynthesisRecipe]:
    return SYNTHESIS_RECIPES.values()


def get_recipe(recipe_id: str) -> SynthesisRecipe:
    try:
        return SYNTHESIS_RECIPES[recipe_id]
    except KeyError as exc:
        raise KeyError(f"Unknown recipe '{recipe_id}'") from exc


__all__ = ["SynthesisRecipe", "SYNTHESIS_RECIPES", "iter_recipes", "get_recipe"]
