"""Permission gate shared by present and future QuestPilot adapters.

An adapter is not enabled merely because its code exists.  It must declare a
non-production environment, a publisher/developer authorization reference,
and a deliberately narrow capability allowlist.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Environment(str, Enum):
    OFFLINE = "offline"
    DEVELOPER_OWNED = "developer_owned"
    PUBLISHER_STAGING = "publisher_staging"
    PRODUCTION = "production"


class ObservationMode(str, Enum):
    SCREEN_OCR = "screen_ocr"
    NATIVE_AGENT = "native_agent"
    OFFICIAL_API = "official_api"


@dataclass(frozen=True)
class AdapterManifest:
    target: str
    environment: Environment
    authorization_reference: str
    observation: ObservationMode
    allowed_capabilities: frozenset[str]


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    reasons: tuple[str, ...]


_BANNED_CAPABILITIES = frozenset(
    {"anti_cheat", "captcha", "chat", "credentials", "payment", "pvp", "trading"}
)


def evaluate_manifest(manifest: AdapterManifest) -> GateDecision:
    reasons: list[str] = []
    if manifest.environment is Environment.PRODUCTION:
        reasons.append("production environments are never eligible")
    if not manifest.authorization_reference.strip():
        reasons.append("missing publisher/developer authorization reference")
    blocked = sorted(manifest.allowed_capabilities & _BANNED_CAPABILITIES)
    if blocked:
        reasons.append("forbidden capabilities requested: " + ", ".join(blocked))
    if not manifest.allowed_capabilities:
        reasons.append("adapter has no explicit capability allowlist")
    return GateDecision(not reasons, tuple(reasons))


MINECRAFT_EDUCATION_MANIFEST = AdapterManifest(
    target="Minecraft Education Code Builder Agent",
    environment=Environment.DEVELOPER_OWNED,
    authorization_reference="https://education.minecraft.net/en-us/lessons/hour-of-ai-the-first-night",
    observation=ObservationMode.NATIVE_AGENT,
    allowed_capabilities=frozenset({"agent.detect", "agent.move", "agent.collectAll", "agent.teleportToPlayer"}),
)


LUANTI_MANIFEST = AdapterManifest(
    target="Luanti local test world",
    environment=Environment.DEVELOPER_OWNED,
    authorization_reference="https://docs.luanti.org/for-creators/creating-mods/",
    observation=ObservationMode.OFFICIAL_API,
    allowed_capabilities=frozenset({"local_command", "world_read", "world_write", "local_status"}),
)
