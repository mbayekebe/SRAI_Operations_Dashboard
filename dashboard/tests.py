import json
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings


class DashboardTests(TestCase):
    databases = set()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

        (self.root / "REGISTRY").mkdir()
        (self.root / "EVIDENCE").mkdir()
        (self.root / "EXAMPLES").mkdir()

        registry = {
            "production_units": [{
                "code": "PU-B03-C01",
                "book": 3,
                "lesson": 1,
                "title": "Neural Network Foundations",
                "operational_status": "published",
                "current_version": "0.2.1",
                "evidence_status": "verified",
                "notes": [],
            }],
            "reconciliation": {"date": "2026-09-11"},
        }

        ecosystem = {
            "executive_pathway_g7_production_acceptance": {
                "module": "EP-M01",
                "version": "0.1",
                "status": "publication_closed",
                "learner_facing_files": 13,
                "final_evidence_source": "EVIDENCE/SRAI_BOOK7_EP_M01_PUBLICATION_ACCEPTANCE.json",
                "linkedin_announcement": "https://example.test/executive-post",
            },
            "book7_ep_m01_publication_closeout": {
                "status": "closed",
                "book7_linkedin": "https://example.test/book7-post",
                "executive_linkedin": "https://example.test/executive-post",
                "evidence_source": "EVIDENCE/SRAI_BOOK7_EP_M01_PUBLICATION_ACCEPTANCE.json",
            },
            "executive_pathway_m03_video_integration": {
                "module": "EP-M03",
                "version": "0.1",
                "status": "deployed_and_owner_accepted",
                "youtube_url": "https://youtu.be/example",
            },
            "executive_pathway_m03_g5_production_acceptance": {
                "module": "EP-M03",
                "version": "0.1",
                "status": "published_with_public_resources_and_tool",
                "module_url": "https://example.test/executive/modules/module-3/",
                "learner_resources_public": 5,
                "executive_tools_public": 1,
            },
            "executive_pathway_m03_publication_acceptance": {
                "module": "EP-M03",
                "version": "0.1",
                "title": "Deciding When Evidence Is Incomplete",
                "status": "publication_closed",
                "website_url": "https://example.test/executive/modules/module-3/",
                "video_url": "https://youtu.be/example",
                "public_asset_publication_authorized": True,
                "evidence_source": "EVIDENCE/SRAI_EP_M03_PUBLICATION_ACCEPTANCE.json",
            },
            "official_statistics_pathway_os_a01_publication_acceptance": {
                "module": "OS-A01",
                "version": "0.1.0-rc3",
                "title": "The National Information Ecosystem",
                "status": "publication_closed",
                "website_url": "https://example.test/official-statistics/modules/a1/",
                "pathway_url": "https://example.test/official-statistics/",
                "video_url": "https://youtu.be/example-os-a01",
                "repository_url": "https://github.com/example/official-statistics",
                "release_url": "https://github.com/example/official-statistics/tree/os-a01-v0.1.0-rc3",
                "educational_linkedin_announcement": "https://example.test/os-announcement",
                "executive_linkedin_announcement": "https://example.test/os-executive",
                "asset_boundary": "Public",
                "published_assets": 10,
                "evidence_source": "EVIDENCE/SRAI_OS_A01_PUBLICATION_ACCEPTANCE.json",
            },
        }

        (self.root / "REGISTRY" / "production_units.json").write_text(
            json.dumps(registry),
            encoding="utf-8",
        )
        (self.root / "REGISTRY" / "ecosystem.json").write_text(
            json.dumps(ecosystem),
            encoding="utf-8",
        )
        (self.root / "EVIDENCE" / "PU-B03-C01_ECOSYSTEM_PUBLICATION.json").write_text(
            json.dumps({"video": {"url": "https://example.test"}}),
            encoding="utf-8",
        )
        (self.root / "EVIDENCE" / "SRAI_BOOK7_EP_M01_PUBLICATION_ACCEPTANCE.json").write_text(
            json.dumps({
                "module": {
                    "title": "Making a Defensible AI Decision",
                    "url": "https://example.test/executive/modules/module-1/",
                    "video_url": "https://youtu.be/module1",
                }
            }),
            encoding="utf-8",
        )
        (self.root / "EVIDENCE" / "SRAI_EP_M03_PUBLICATION_ACCEPTANCE.json").write_text(
            json.dumps({"status": "PUBLICATION_CLOSED"}),
            encoding="utf-8",
        )
        (self.root / "EVIDENCE" / "SRAI_OS_A01_PUBLICATION_ACCEPTANCE.json").write_text(
            json.dumps({"status": "PUBLICATION_CLOSED"}),
            encoding="utf-8",
        )
        (self.root / "EXAMPLES" / "PU-B03-C01_LESSON_MANIFEST.json").write_text(
            "{}",
            encoding="utf-8",
        )

        self.override = override_settings(OPERATIONS_ROOT=self.root)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        self.tmp.cleanup()

    def test_overview(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PU-B03-C01")
        self.assertContains(response, "green")
        self.assertContains(response, "Executive Pathway modules")
        self.assertContains(response, "EP-M01")
        self.assertContains(response, "Making a Defensible AI Decision")
        self.assertContains(response, "EP-M03")
        self.assertContains(response, "Deciding When Evidence Is Incomplete")
        self.assertContains(response, "Public")
        self.assertContains(response, "Official Statistics &amp; AI modules")
        self.assertContains(response, "OS-A01")
        self.assertContains(response, "The National Information Ecosystem")
        self.assertContains(response, "10 published assets")

    def test_detail(self):
        response = self.client.get("/unit/PU-B03-C01/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Neural Network Foundations")

    def test_health_json(self):
        response = self.client.get("/health.json")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        modules = {
            item["code"]: item
            for item in response.json()["executive_modules"]
        }
        self.assertEqual(set(modules), {"EP-M01", "EP-M03"})
        self.assertEqual(modules["EP-M01"]["health"], "green")
        self.assertEqual(modules["EP-M03"]["health"], "green")
        official_modules = {
            item["code"]: item
            for item in response.json()["official_statistics_modules"]
        }
        self.assertEqual(set(official_modules), {"OS-A01"})
        self.assertEqual(official_modules["OS-A01"]["health"], "green")
