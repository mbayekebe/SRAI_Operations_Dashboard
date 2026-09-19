from collections import Counter

from django.http import Http404, JsonResponse
from django.shortcuts import render

from .services import load_snapshot, load_unit


def overview(request):
    snap = load_snapshot()

    q = request.GET.get("q", "").strip().lower()
    book = request.GET.get("book", "").strip()
    status = request.GET.get("status", "").strip().lower()
    health = request.GET.get("health", "").strip().lower()

    units = snap.units

    if q:
        units = [
            unit for unit in units
            if q in (
                f"{unit.get('code', '')} "
                f"{unit.get('title', '')} "
                f"{unit.get('repository', '')}"
            ).lower()
        ]

    if book:
        units = [unit for unit in units if str(unit.get("book", "")) == book]

    if status:
        units = [
            unit for unit in units
            if str(unit.get("operational_status", "")).lower() == status
        ]

    if health:
        units = [unit for unit in units if unit.get("health") == health]

    counts = Counter(unit.get("health") for unit in snap.units)
    executive_counts = Counter(module.get("health") for module in snap.modules)
    status_counts = Counter(
        str(unit.get("operational_status", "unknown")).lower()
        for unit in snap.units
    )
    books = sorted({
        unit.get("book")
        for unit in snap.units
        if unit.get("book") is not None
    })

    return render(request, "dashboard/overview.html", {
        "snapshot": snap,
        "units": units,
        "modules": snap.modules,
        "counts": counts,
        "executive_counts": executive_counts,
        "status_counts": status_counts,
        "books": books,
        "filters": {
            "q": request.GET.get("q", ""),
            "book": book,
            "status": status,
            "health": health,
        },
    })


def unit_detail(request, code):
    snap, unit, evidence, manifest = load_unit(code)

    if not unit:
        raise Http404("Production unit not found")

    return render(request, "dashboard/unit_detail.html", {
        "snapshot": snap,
        "unit": unit,
        "evidence": evidence,
        "manifest": manifest,
    })


def health_json(request):
    snap = load_snapshot()

    return JsonResponse({
        "ok": not snap.errors,
        "root": str(snap.root),
        "errors": snap.errors,
        "units": [
            {
                "code": unit.get("code"),
                "status": unit.get("operational_status"),
                "health": unit.get("health"),
            }
            for unit in snap.units
        ],
        "executive_modules": [
            {
                "code": module.get("code"),
                "status": module.get("status"),
                "health": module.get("health"),
            }
            for module in snap.modules
        ],
    })
