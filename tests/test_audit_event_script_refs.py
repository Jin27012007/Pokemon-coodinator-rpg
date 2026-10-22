from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import audit_event_script_refs as audit


class EventAuditHelperTests(unittest.TestCase):
    def test_strip_comments_preserves_comment_markers_inside_strings(self):
        source = 'msgbox "hello @ world // still text" @ actual comment\nend\n'
        self.assertEqual(
            audit.strip_comments(source),
            'msgbox "hello @ world // still text" \nend',
        )

    def test_flow_target_reads_conditional_jump_label(self):
        self.assertEqual(
            audit.flow_target("goto_if_eq", "VAR_RESULT, MALE, Scene_EventScript_Female"),
            "Scene_EventScript_Female",
        )

    def test_flow_target_reads_trainer_branch_label(self):
        self.assertEqual(
            audit.flow_target("call_if_defeated", "TRAINER_MAY, Scene_EventScript_AfterBattle"),
            "Scene_EventScript_AfterBattle",
        )

    def test_collect_script_fields_walks_nested_map_data(self):
        obj = {
            "object_events": [{"script": "NPC_EventScript_Talk"}],
            "warp_events": [{"script": "0"}],
            "nested": {"events": [{"script": "Coord_EventScript_Enter"}]},
        }
        self.assertEqual(
            list(audit.collect_script_fields(obj)),
            [
                ("object_events[0].script", "NPC_EventScript_Talk"),
                ("warp_events[0].script", "0"),
                ("nested.events[0].script", "Coord_EventScript_Enter"),
            ],
        )

    def test_contiguous_movement_offset_labels_are_one_stream(self):
        bodies = {
            "Scene_Movement_Enter": [("fixture.inc", "walk_right\n", 10)],
            "Scene_Movement_StepForward": [("fixture.inc", "walk_right\nstep_end\n", 11)],
            "Scene_EventScript_Next": [("fixture.inc", "end\n", 13)],
        }
        self.assertEqual(audit.find_movement_terminator_candidates(bodies), [])

    def test_unterminated_movement_before_event_label_is_reported(self):
        bodies = {
            "Scene_Movement_Broken": [("fixture.inc", "walk_left\n", 10)],
            "Scene_EventScript_Next": [("fixture.inc", "end\n", 11)],
        }
        self.assertEqual(
            audit.find_movement_terminator_candidates(bodies),
            [("fixture.inc", 10, "Scene_Movement_Broken", "walk_left")],
        )

    def test_macro_risk_respects_conditional_callnative_waitstate(self):
        source = r"""
.macro callnative func:req, requests_effects=0, waitstate=0
.if \\waitstate
waitstate implicit=1
.endif
.endm
.macro getdaycaregfx
callnative GetDaycareGraphics, requests_effects=1
.endm
.macro blockingnative
callnative GetDaycareGraphics, requests_effects=1, waitstate=1
.endm
"""
        with tempfile.TemporaryDirectory() as directory:
            macro_file = Path(directory) / "event.inc"
            macro_file.write_text(source)
            risks = audit.macro_risk_catalog(macro_file, set())
        self.assertNotIn("context", risks["callnative"])
        self.assertNotIn("context", risks["getdaycaregfx"])
        self.assertIn("context", risks["blockingnative"])

    def test_dynamic_warp_is_explicitly_classified(self):
        self.assertTrue(audit.is_dynamic_map_reference("MAP_DYNAMIC"))
        self.assertFalse(audit.is_dynamic_map_reference("MAP_LILYCOVE_CITY"))


if __name__ == "__main__":
    unittest.main()
