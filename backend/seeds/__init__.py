"""Database seeding package for PWD301."""

from __future__ import annotations

from backend.seeds.baseline import seed_baseline
from backend.seeds.demo import seed_demo

__all__ = ["seed_baseline", "seed_demo"]
