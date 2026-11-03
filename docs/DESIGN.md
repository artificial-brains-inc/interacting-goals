# Design and body contract

The public design has 55 populations and 74 directed connections. Of these,
four populations and five connections form an isolated ACK circuit. The
remaining 51 populations and 69 connections carry the experiment's observations,
sensory processing, goal interactions and motor outputs.

## Operating points

| Population group | Rhythm / TNorm | Role |
| --- | --- | --- |
| Input relays | High-gamma / 10 | Carry external observations |
| `CAMERA_T1`, six sensory `*_T1` populations | Theta / 3 | First sensory stage |
| `CAMERA_T2_LEFT`, `CAMERA_T2_RIGHT`, six sensory `*_T2` populations | Theta / 2.01 | Second stage; selected targets of inhibition |
| `FORWARD_*`, `A_TURN_*`, `SIDE_TURN_*`, `LIGHT_VALUE_*` | Beta / 5 | Motor support or sensory evidence |
| `LIGHT_COMPARE_LEFT`, `LIGHT_COMPARE_RIGHT` | Beta / 3 | Paired signed light comparisons |
| `FRONT_ANY`, `BLOCK_LIGHT_*`, `SIDE_ANY`, `LIGHT_ANY`, `OBSTACLE_ANY`, `ANY_GOAL` | Beta / 8 | Two-input OR operators |
| `SEARCH_RESET` | Beta / 2 | Right-motor reset feedback |
| ACK relay and clearing population | High-gamma / 10 | Input acknowledgement and clearing |

Each OR input has `role="operand", units=1`. The comparisons likewise use one
positive operand from their own side and one negative operand from the opposite
side. This is the experiment's paired directional comparison circuit; it is not
a claim that every Boolean XOR uses this construction.

`ANY_GOAL → SEARCH_RESET` is inhibitory with `strength=2.5`.
Other inhibitory edges use the SDK's reference strength of 1. The return from
`SEARCH_RESET` to `CAMERA_T2_RIGHT` is marked `role="feedback"`.
The SDK calculates the executable connections from the public design.

## Inputs

| Input | Width | Webots device / encoding |
| --- | ---: | --- |
| `CAMERA` | 64 | `camera`: 8×8 sample centers, RGB mean divided by 255 |
| `FRONT_LEFT` | 16 | `proximity_left`: raw value / `proximity_full_scale` |
| `FRONT_RIGHT` | 16 | `proximity_right`: same scaling |
| `SIDE_LEFT` | 16 | `proximity_left_side`: same scaling |
| `SIDE_RIGHT` | 16 | `proximity_right_side`: same scaling |
| `LIGHT_LEFT` | 16 | `light_left`: world lookup table supplies a value on 0..1 scale |
| `LIGHT_RIGHT` | 16 | `light_right`: same scale |
| `COLLISION` | 1 | Reserved input, always zero; relay has no behavioral outgoing connection |
| `TRANSPORT_ACK` | 1 | Marker sent atomically with each observation |

Proximity and light values are clamped to 0..1. The first `round(level × 16)`
positions are 1 and the rest are 0, using Python's round-to-even behavior.
The host does not subtract left/right readings or select the stronger side.

## Outputs

| Output | Effect |
| --- | --- |
| `WHEEL_LEFT` | Actual bistable state 0 or 1 maps to 0 or `wheel_speed_rad_s` on `left wheel motor` |
| `WHEEL_RIGHT` | Same mapping on `right wheel motor` |
| `TRANSPORT_ACK_OUT` | Acknowledges the sensor marker; no motor connection |

Right active with left suppressed turns left; left active with right suppressed
turns right. There is no software output hold, winner selection or reverse command.

## World and stimulus

`worlds/interacting_goals.wbt` uses a 16 ms basic physics interval and includes
all robot devices and geometry. The light supervisor runs inside Webots and
changes the stimulus using simulation time. With the normal launch command:

- Candidate light offsets are +35°, −35°, +90° and −90° relative to robot heading.
- A target is nominally 0.70 m away, constrained by the supervisor's bounds.
- A narrow beam is aimed toward the nearer light sensor.
- A switch requires alignment within 14° and approach of at least 0.010 m/s
  maintained for 0.35 simulation seconds, after the 0.70-second dwell condition.
- The light then stays off for four simulation seconds before the next target.

This supervisor constructs an experimental stimulus. The brain is not given
pose, heading error, target coordinates or the supervisor's completion condition.
The supervisor never writes motor commands.

For repeatable target choices you can set a seed before running:

```bash
export AB_LURE_SEED=1
ab run -ab --env .env
```

This controls stimulus selection, not neural state or a guaranteed identical
trajectory. Without a seed, the supervisor uses system randomness.
