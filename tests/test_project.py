import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ab import Brain
from design_brain import create_brain, ROOT
from goals.sensors import proximity_vector, load_config
from goals.motors import MotorCommands
from goals.transport import EventBuffer, StopRequested
from goals.lifecycle import require_installed
from goals.application import saved_design, WORLD_PATH
from goals.contracts import ACK_OUTPUT, INPUT_SIZES


def output(step, left, right, ack=0):
    return {"step": step, "actuation": {"channels": {
        "WHEEL_LEFT": left, "WHEEL_RIGHT": right, ACK_OUTPUT: ack}}}


def report(state="READY", digest="expected", busy=False):
    return {"engine": {"state": state, "has_brain": True, "busy": busy},
            "package": {"active": {"design_sha256": digest}}}


class DesignTests(unittest.TestCase):
    def test_public_design_roundtrip(self):
        brain = create_brain()
        brain.validate()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "brain.abdesign.json"
            brain.save(path)
            self.assertEqual(Brain.load(path).to_dict(), brain.to_dict())
        Brain.load(ROOT / "brain.abdesign.json").validate()



class TranslationTests(unittest.TestCase):
    def test_movement_duration_accepts_multiples_of_world_basic_step(self):
        config = load_config()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch("goals.sensors.ROOT", root):
                for step in (16, 32, 64, 128):
                    with self.subTest(step=step):
                        (root / "config.json").write_text(json.dumps(dict(config, physics_step_ms=step)))
                        self.assertEqual(load_config()["physics_step_ms"], step)
                for step in (0, -16, 8, 24, 16.0, True, None):
                    with self.subTest(step=step):
                        (root / "config.json").write_text(json.dumps(dict(config, physics_step_ms=step)))
                        with self.assertRaisesRegex(ValueError, "multiple of 16"):
                            load_config()

    def test_proximity_scale_saturation_and_direction(self):
        for raw, active in ((0, 0), (250, 4), (500, 8), (1000, 16), (1500, 16)):
            values = proximity_vector(raw, 1000)
            self.assertEqual(values, [1.0] * active + [0.0] * (16 - active))
        for raw in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                proximity_vector(raw, 1000)

    def test_real_sdk_decodes_turns_and_zero_clears_previous_motion(self):
        commands = MotorCommands(3.0)
        self.assertEqual(commands.apply(output(1, 1, 1)), {"WHEEL_LEFT": 3.0, "WHEEL_RIGHT": 3.0})
        self.assertEqual(commands.apply(output(2, 0, 1)), {"WHEEL_LEFT": 0.0, "WHEEL_RIGHT": 3.0})
        self.assertEqual(commands.apply(output(3, 1, 0)), {"WHEEL_LEFT": 3.0, "WHEEL_RIGHT": 0.0})
        self.assertEqual(commands.apply(output(4, 0, 0)), {"WHEEL_LEFT": 0.0, "WHEEL_RIGHT": 0.0})
        with self.assertRaises(ValueError):
            commands.apply(output(4, 1, 1))

    def test_bad_output_contract_does_not_become_motion(self):
        for event in ({"step": 1}, output(1, 2, 0), output(1, True, 0)):
            with self.assertRaises(ValueError):
                MotorCommands(3).apply(event)

    def test_output_buffer_preserves_zero_and_detects_missing_step(self):
        events = EventBuffer()
        events.on_output(output(10, 1, 1))
        events.on_output(output(11, 0, 0))
        self.assertEqual(events.take_one()[0][1]["step"], 10)
        self.assertEqual(events.take_one()[0][1]["actuation"]["channels"]["WHEEL_LEFT"], 0)
        self.assertEqual(events.take_one(), [])
        events.on_output(output(13, 1, 1))
        with self.assertRaises(RuntimeError):
            events.take_one()

    def test_timeout_and_remote_stop(self):
        clock = [0.0]
        events = EventBuffer(timeout_seconds=5, clock=lambda: clock[0])
        clock[0] = 5.1
        with self.assertRaises(RuntimeError):
            events.take_one()
        events = EventBuffer()
        events.on_control({"command": "stop"})
        with self.assertRaises(StopRequested):
            events.take_one()


class LifecycleTests(unittest.TestCase):
    def test_run_rejects_running_busy_or_wrong_brain(self):
        self.assertEqual(require_installed(report(), "expected"), "READY")
        for item in (report("RUNNING"), report(busy=True), report(digest="other")):
            with self.assertRaises(RuntimeError):
                require_installed(item, "expected")

    def test_designer_edit_is_loaded_without_regenerating_python_design(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            edited = create_brain().to_dict()
            next(node for node in edited["nodes"] if node["name"] == "A_TURN_LEFT")["tnorm"] = 4.9
            Brain.from_dict(edited).save(root / "brain.abdesign.json")
            loaded = saved_design(root).to_dict()
            self.assertEqual(next(node for node in loaded["nodes"] if node["name"] == "A_TURN_LEFT")["tnorm"], 4.9)


if __name__ == "__main__":
    unittest.main()
