"""Measurements and fixed encodings; action selection belongs to the brain."""
import json
import math
from pathlib import Path
from .contracts import WHEEL_OUTPUTS as OUTPUTS

ROOT = Path(__file__).resolve().parents[1]
WORLD_BASIC_STEP_MS = 16


def load_config():
    config = json.loads((ROOT / "config.json").read_text())
    step = config.get("physics_step_ms")
    if type(step) is not int or step <= 0 or step % WORLD_BASIC_STEP_MS:
        raise ValueError("physics_step_ms must be a positive integer multiple of 16 ms (for example 16, 32 or 64).")
    for key in ("proximity_full_scale", "wheel_speed_rad_s", "output_timeout_seconds", "ack_timeout_seconds"):
        value = config.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"{key} must be positive and finite.")
    if config["wheel_speed_rad_s"] > 8:
        raise ValueError("The included wheels have an 8 rad/s physical maximum.")
    return config


def proximity_vector(raw, full_scale, width=16):
    if not math.isfinite(raw) or not math.isfinite(full_scale) or full_scale <= 0:
        raise ValueError("Invalid proximity measurement or full scale.")
    level = max(0.0, min(1.0, raw / full_scale))
    active = max(0, min(width, int(round(level * width))))
    return [1.0] * active + [0.0] * (width - active)


class Sensors:
    DEVICES = {
        "FRONT_LEFT": ("proximity_left", "proximity_full_scale"),
        "FRONT_RIGHT": ("proximity_right", "proximity_full_scale"),
        "SIDE_LEFT": ("proximity_left_side", "proximity_full_scale"),
        "SIDE_RIGHT": ("proximity_right_side", "proximity_full_scale"),
        "LIGHT_LEFT": ("light_left", None),
        "LIGHT_RIGHT": ("light_right", None),
    }

    def __init__(self, robot, step):
        self.camera = robot.getDevice("camera")
        self.values = {name: robot.getDevice(device) for name, (device, _) in self.DEVICES.items()}
        for sensor in (self.camera, *self.values.values()):
            if sensor is None:
                raise RuntimeError("The world is missing a required sensor.")
            sensor.enable(step)

    def capture(self, config):
        from controller import Camera
        image = self.camera.getImage()
        if image is None:
            raise RuntimeError("Camera frame is not available yet.")
        width, height = self.camera.getWidth(), self.camera.getHeight()
        pixels = []
        for row in range(8):
            y = min(height - 1, int((row + 0.5) * height / 8))
            for column in range(8):
                x = min(width - 1, int((column + 0.5) * width / 8))
                pixels.append((Camera.imageGetRed(image, width, x, y)
                               + Camera.imageGetGreen(image, width, x, y)
                               + Camera.imageGetBlue(image, width, x, y)) / 765.0)
        frame = {"CAMERA": pixels, "COLLISION": [0.0]}
        observation = {"camera_mean": sum(pixels) / len(pixels)}
        for name, sensor in self.values.items():
            device, scale_key = self.DEVICES[name]
            raw = float(sensor.getValue())
            frame[name] = proximity_vector(raw, config[scale_key] if scale_key else 1.0)
            observation[device] = raw
        return frame, observation
