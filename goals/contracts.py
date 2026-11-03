"""Named public populations shared by the robot and transport adapters."""
ACK_INPUT = "TRANSPORT_ACK"
ACK_OUTPUT = "TRANSPORT_ACK_OUT"
WHEEL_OUTPUTS = ("WHEEL_LEFT", "WHEEL_RIGHT")
INPUT_SIZES = {"CAMERA": 64, "COLLISION": 1, "FRONT_LEFT": 16, "FRONT_RIGHT": 16,
               "SIDE_LEFT": 16, "SIDE_RIGHT": 16, "LIGHT_LEFT": 16, "LIGHT_RIGHT": 16,
               ACK_INPUT: 1}
OUTPUT_SIZES = {name: 1 for name in (*WHEEL_OUTPUTS, ACK_OUTPUT)}
