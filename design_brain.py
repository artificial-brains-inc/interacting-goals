"""Build the public design for interacting avoidance, approach and search goals."""
from pathlib import Path
from ab import Brain

ROOT = Path(__file__).resolve().parent


def relay(brain, name, width):
    brain.input(name, width)
    brain.opu(name + "_RELAY", "high-gamma", 10)
    brain.connect(name, name + "_RELAY")
    return name + "_RELAY"


def sensory_path(brain, name):
    source = relay(brain, name, 16)
    brain.opu(name + "_T1", "theta", 3)
    brain.opu(name + "_T2", "theta", 2.01)
    brain.connect(source, name + "_T1")
    brain.connect(name + "_T1", name + "_T2")
    return name + "_T2"


def either(brain, name, first, second):
    """Each source supplies one complete operand to this example's Beta T8 OR."""
    brain.opu(name, "beta", 8)
    brain.connect(first, name, role="operand", units=1)
    brain.connect(second, name, role="operand", units=1)
    return name


def create_brain():
    brain = Brain("Interacting Goals")
    # Shared scene drive, with independent second stages for the two motors.
    camera = relay(brain, "CAMERA", 64)
    brain.opu("CAMERA_T1", "theta", 3)
    brain.connect(camera, "CAMERA_T1")
    for side in ("LEFT", "RIGHT"):
        brain.opu("CAMERA_T2_" + side, "theta", 2.01)
        brain.opu("FORWARD_" + side, "beta", 5)
        brain.output("WHEEL_" + side)
        brain.connect("CAMERA_T1", "CAMERA_T2_" + side)
        brain.connect("CAMERA_T2_" + side, "FORWARD_" + side)
        brain.connect("FORWARD_" + side, "WHEEL_" + side)

    # Reserved observation, supplied as zero; it does not select an action.
    relay(brain, "COLLISION", 1)

    # Front obstacles recruit actual turn actions. Side obstacles provide
    # contextual evidence for the light gates; they have no direct motor edge.
    for prefix, turn in (("FRONT", "A_TURN"), ("SIDE", "SIDE_TURN")):
        for side, opposite in (("RIGHT", "LEFT"), ("LEFT", "RIGHT")):
            evidence = sensory_path(brain, prefix + "_" + side)
            brain.opu(turn + "_" + opposite, "beta", 5)
            brain.connect(evidence, turn + "_" + opposite)
        brain.connect(turn + "_LEFT", turn + "_RIGHT", "inh")
        brain.connect(turn + "_RIGHT", turn + "_LEFT", "inh")
    for side in ("LEFT", "RIGHT"):
        brain.connect("A_TURN_" + side, "FORWARD_" + side, "inh")
        brain.connect("A_TURN_" + side, "WHEEL_" + side, "inh")

    # Approach the brighter side. These are two signed comparisons, each
    # with matched positive and negative operands, rather than a host argmax.
    for side in ("LEFT", "RIGHT"):
        evidence = sensory_path(brain, "LIGHT_" + side)
        brain.opu("LIGHT_VALUE_" + side, "beta", 5)
        brain.connect(evidence, "LIGHT_VALUE_" + side)
        brain.opu("LIGHT_COMPARE_" + side, "beta", 3)
    for side, opposite in (("LEFT", "RIGHT"), ("RIGHT", "LEFT")):
        target = "LIGHT_COMPARE_" + side
        brain.connect("LIGHT_VALUE_" + side, target, role="operand", units=1)
        brain.connect("LIGHT_VALUE_" + opposite, target, "inh", role="operand", units=1)
        brain.connect(target, "FORWARD_" + side, "inh")
        brain.connect(target, "WHEEL_" + side, "inh")

    # Front activity blocks both approach channels; side evidence blocks
    # only the light turn that would move toward that side's obstacle.
    either(brain, "FRONT_ANY", "A_TURN_LEFT", "A_TURN_RIGHT")
    either(brain, "BLOCK_LIGHT_LEFT", "FRONT_ANY", "SIDE_TURN_RIGHT")
    either(brain, "BLOCK_LIGHT_RIGHT", "FRONT_ANY", "SIDE_TURN_LEFT")
    brain.connect("BLOCK_LIGHT_LEFT", "LIGHT_LEFT_T2", "inh")
    brain.connect("BLOCK_LIGHT_RIGHT", "LIGHT_RIGHT_T2", "inh")

    # Search is a right-motor reset loop. Detected goal activity suppresses
    # that reset, allowing sensor-driven action to take over.
    either(brain, "SIDE_ANY", "SIDE_TURN_LEFT", "SIDE_TURN_RIGHT")
    either(brain, "LIGHT_ANY", "LIGHT_VALUE_LEFT", "LIGHT_VALUE_RIGHT")
    either(brain, "OBSTACLE_ANY", "FRONT_ANY", "SIDE_ANY")
    either(brain, "ANY_GOAL", "OBSTACLE_ANY", "LIGHT_ANY")
    brain.opu("SEARCH_RESET", "beta", 2)
    brain.connect("FORWARD_RIGHT", "SEARCH_RESET")
    brain.connect("ANY_GOAL", "SEARCH_RESET", "inh", strength=2.5)
    brain.connect("SEARCH_RESET", "CAMERA_T2_RIGHT", "inh", role="feedback")
    brain.connect("SEARCH_RESET", "WHEEL_RIGHT", "inh")

    # The transport circuit is isolated from every behavioral pathway.
    brain.input("TRANSPORT_ACK", 1)
    brain.opu("TRANSPORT_ACK_RELAY", "high-gamma", 10)
    brain.output("TRANSPORT_ACK_OUT")
    brain.opu("TRANSPORT_ACK_CLEAR", "high-gamma", 10)
    brain.connect("TRANSPORT_ACK", "TRANSPORT_ACK_RELAY")
    brain.connect("TRANSPORT_ACK_RELAY", "TRANSPORT_ACK_OUT")
    brain.connect("TRANSPORT_ACK_OUT", "TRANSPORT_ACK_CLEAR")
    brain.connect("TRANSPORT_ACK_CLEAR", "TRANSPORT_ACK_OUT", "inh")
    brain.connect("TRANSPORT_ACK_CLEAR", "TRANSPORT_ACK_CLEAR", "inh", role="feedback")

    # Positions affect the Canvas, not neural behavior.
    positions = {
        "CAMERA": (40, 60), "CAMERA_RELAY": (320, 60), "CAMERA_T1": (600, 60),
        "CAMERA_T2_LEFT": (880, 60), "CAMERA_T2_RIGHT": (880, 220),
        "FORWARD_LEFT": (1160, 60), "FORWARD_RIGHT": (1160, 220),
        "WHEEL_LEFT": (1440, 60), "WHEEL_RIGHT": (1440, 220),
        "FRONT_ANY": (1720, 430),
        "BLOCK_LIGHT_LEFT": (2000, 740), "BLOCK_LIGHT_RIGHT": (2000, 900),
        "SIDE_ANY": (1720, 1100), "LIGHT_ANY": (1720, 1370),
        "OBSTACLE_ANY": (2000, 1130), "ANY_GOAL": (2280, 1220),
        "SEARCH_RESET": (2280, 220),
        "COLLISION": (40, 1510), "COLLISION_RELAY": (320, 1510),
        "TRANSPORT_ACK": (40, 1730), "TRANSPORT_ACK_RELAY": (320, 1730),
        "TRANSPORT_ACK_OUT": (600, 1730), "TRANSPORT_ACK_CLEAR": (880, 1730),
    }
    rows = [("FRONT_RIGHT", "A_TURN_LEFT", 430), ("FRONT_LEFT", "A_TURN_RIGHT", 590),
            ("LIGHT_LEFT", "LIGHT_VALUE_LEFT", 800), ("LIGHT_RIGHT", "LIGHT_VALUE_RIGHT", 960),
            ("SIDE_RIGHT", "SIDE_TURN_LEFT", 1170), ("SIDE_LEFT", "SIDE_TURN_RIGHT", 1330)]
    for sensor, result, y in rows:
        for suffix, x in (("", 40), ("_RELAY", 320), ("_T1", 600), ("_T2", 880)):
            positions[sensor + suffix] = (x, y)
        positions[result] = (1160, y)
    positions["LIGHT_COMPARE_LEFT"] = (1440, 800)
    positions["LIGHT_COMPARE_RIGHT"] = (1440, 960)
    design = brain.to_dict()
    for node in design["nodes"]:
        node["x"], node["y"] = positions[node["name"]]
    return Brain.from_dict(design)


if __name__ == "__main__":
    create_brain().save(ROOT / "brain.abdesign.json")
    print("Saved brain.abdesign.json. Inspect with ab design, then build on Prima-Lux.")
