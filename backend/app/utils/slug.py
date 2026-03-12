from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable


class SlugError(ValueError):
    pass


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)

    if not slug:
        raise SlugError("Slug cannot be empty.")

    return slug


def generate_unique_slug(
    *,
    source_value: str,
    slug_value: str | None,
    exists: Callable[[str], bool],
) -> str:
    base_slug = slugify(slug_value or source_value)
    candidate = base_slug
    suffix = 2

    while exists(candidate):
        candidate = f"{base_slug}-{suffix}"
        suffix += 1

    return candidate
