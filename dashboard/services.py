import json
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings


@dataclass
class Snapshot:
    root: Path
    units: list[dict] = field(default_factory=list)
    modules: list[dict] = field(default_factory=list)
    reconciliation: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def read_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def health_for(unit):
    status = str(unit.get("operational_status", "")).lower()
    evidence = str(unit.get("evidence_status", "")).lower()
    notes = " ".join(unit.get("notes") or []).lower()

    if any(word in status + " " + evidence for word in ("failed", "blocked", "invalid")):
        return "red"
    if status in {"planned", "draft", "not_started"}:
        return "grey"
    if status == "published" and evidence in {"verified", "pass", "passed"}:
        return "amber" if "follow-up" in notes or "followup" in notes or "not_reverified" in notes else "green"
    return "amber"


def executive_health(record):
    status = str(record.get("status", "")).lower()

    if any(word in status for word in ("failed", "blocked", "invalid")):
        return "red"
    if status in {"publication_closed", "deployed_and_owner_accepted"}:
        return "green"
    if status in {"planned", "draft", "not_started"}:
        return "grey"
    return "amber"


def load_executive_modules(root, snap):
    ecosystem_path = root / "REGISTRY" / "ecosystem.json"

    if not ecosystem_path.exists():
        return

    try:
        ecosystem = read_json(ecosystem_path)
    except (OSError, json.JSONDecodeError) as exc:
        snap.errors.append(f"Executive registry could not be read: {exc}")
        return

    for key, publication in ecosystem.items():
        if not (
            key.startswith("executive_pathway_m")
            and key.endswith("_publication_acceptance")
            and isinstance(publication, dict)
        ):
            continue

        code = str(publication.get("module", ""))
        if not code.startswith("EP-M"):
            continue

        number = code.split("-M", 1)[-1]
        production = (
            ecosystem.get(f"executive_pathway_m{number}_g5_production_acceptance")
            or ecosystem.get(f"executive_pathway_m{number}_g7_production_acceptance")
            or {}
        )
        video = ecosystem.get(f"executive_pathway_m{number}_video_integration") or {}

        evidence_source = publication.get("evidence_source", "")
        evidence_path = root / evidence_source if evidence_source else None

        public_assets = bool(publication.get("public_asset_publication_authorized"))
        if public_assets:
            asset_boundary = "Public"
        elif production.get("controlled_downloads_public") is False:
            asset_boundary = "Controlled"
        else:
            asset_boundary = "Recorded"

        snap.modules.append({
            "code": code,
            "title": publication.get("title", ""),
            "version": publication.get("version", ""),
            "status": publication.get("status", "unknown"),
            "health": executive_health(publication),
            "website_url": publication.get("website_url") or production.get("module_url"),
            "video_url": publication.get("video_url") or video.get("youtube_url"),
            "educational_linkedin": publication.get("educational_linkedin_announcement"),
            "executive_linkedin": publication.get("executive_linkedin_announcement"),
            "asset_boundary": asset_boundary,
            "learner_resources": production.get("learner_resources_public")
                or production.get("learner_resources_described"),
            "executive_tools": production.get("executive_tools_public"),
            "evidence_source": evidence_source,
            "evidence_file_exists": bool(evidence_path and evidence_path.exists()),
        })

    legacy_production = ecosystem.get(
        "executive_pathway_g7_production_acceptance"
    ) or {}
    legacy_closeout = ecosystem.get(
        "book7_ep_m01_publication_closeout"
    ) or {}

    if (
        legacy_production.get("module") == "EP-M01"
        and not any(item["code"] == "EP-M01" for item in snap.modules)
    ):
        evidence_source = (
            legacy_closeout.get("evidence_source")
            or legacy_production.get("final_evidence_source")
            or legacy_production.get("evidence_source")
            or ""
        )
        evidence_path = root / evidence_source if evidence_source else None
        evidence = {}

        try:
            if evidence_path and evidence_path.exists():
                evidence = read_json(evidence_path)
        except (OSError, json.JSONDecodeError) as exc:
            snap.errors.append(f"EP-M01 evidence file error: {exc}")

        module_record = evidence.get("module") or {}

        snap.modules.append({
            "code": "EP-M01",
            "title": module_record.get(
                "title",
                "Making a Defensible AI Decision",
            ),
            "version": legacy_production.get("version", "0.1"),
            "status": legacy_production.get(
                "status",
                legacy_closeout.get("status", "unknown"),
            ),
            "health": executive_health(legacy_production),
            "website_url": module_record.get(
                "url",
                "https://srai.mbayekebe.net/executive/modules/module-1/",
            ),
            "video_url": module_record.get("video_url"),
            "educational_linkedin": legacy_closeout.get("book7_linkedin"),
            "executive_linkedin": (
                legacy_closeout.get("executive_linkedin")
                or legacy_production.get("linkedin_announcement")
            ),
            "asset_boundary": "Public + controlled",
            "learner_resources": legacy_production.get(
                "learner_facing_files"
            ),
            "executive_tools": 1,
            "evidence_source": evidence_source,
            "evidence_file_exists": bool(
                evidence_path and evidence_path.exists()
            ),
        })

    snap.modules.sort(key=lambda item: item["code"])


def load_snapshot(root=None):
    root = Path(root or settings.OPERATIONS_ROOT)
    snap = Snapshot(root=root)

    registry_path = root / "REGISTRY" / "production_units.json"

    if not registry_path.exists():
        snap.errors.append(f"Registry not found: {registry_path}")
        load_executive_modules(root, snap)
        return snap

    try:
        data = read_json(registry_path)
    except (OSError, json.JSONDecodeError) as exc:
        snap.errors.append(f"Registry could not be read: {exc}")
        load_executive_modules(root, snap)
        return snap

    units = data.get("production_units")

    if not isinstance(units, list):
        snap.errors.append("Registry field 'production_units' must be a list.")
        load_executive_modules(root, snap)
        return snap

    snap.reconciliation = data.get("reconciliation") or {}

    for raw in units:
        unit = dict(raw)
        unit["health"] = health_for(unit)

        code = unit.get("code", "")
        evidence_path = root / "EVIDENCE" / f"{code}_ECOSYSTEM_PUBLICATION.json"
        manifest_path = root / "EXAMPLES" / f"{code}_LESSON_MANIFEST.json"

        unit["evidence_file_exists"] = evidence_path.exists()
        unit["manifest_file_exists"] = manifest_path.exists()
        unit["evidence_path"] = str(evidence_path)
        unit["manifest_path"] = str(manifest_path)

        snap.units.append(unit)

    load_executive_modules(root, snap)
    return snap


def load_unit(code, root=None):
    snap = load_snapshot(root)
    unit = next(
        (item for item in snap.units if item.get("code", "").lower() == code.lower()),
        None,
    )

    if not unit:
        return snap, None, None, None

    evidence = manifest = None

    try:
        if unit["evidence_file_exists"]:
            evidence = read_json(Path(unit["evidence_path"]))
    except (OSError, json.JSONDecodeError) as exc:
        snap.errors.append(f"Evidence file error: {exc}")

    try:
        if unit["manifest_file_exists"]:
            manifest = read_json(Path(unit["manifest_path"]))
    except (OSError, json.JSONDecodeError) as exc:
        snap.errors.append(f"Manifest file error: {exc}")

    return snap, unit, evidence, manifest
