# Building a goal and choosing its interactions

A goal needs a condition to pursue, evidence about that condition, actions that
can help, and a way to stop or reconsider those actions. Connecting goals means
choosing where their evidence and actions should interact.

## Work through one conflict

The light is to the right and an obstacle is in front-right space.

| Question | Answer in this design |
| --- | --- |
| What supports approach? | The right light pathway feeds `LIGHT_VALUE_RIGHT` and its comparison. |
| How does approach turn right? | `LIGHT_COMPARE_RIGHT` inhibits the right motor and wheel. |
| What supports avoidance? | `FRONT_RIGHT_T2` excites `A_TURN_LEFT`. |
| How does avoidance turn left? | `A_TURN_LEFT` inhibits the left motor and wheel. |
| What conflict appears if both act? | Both wheels may be inhibited, preventing either useful turn. |
| Where is priority expressed? | `FRONT_ANY` feeds both light-blocking operators, which inhibit the light Theta T2.01 populations. |
| What allows approach to resume? | Front evidence and its blocking activity must subside as the body moves away. |
| What must be observed? | Suppression of approach, a useful physical avoidance turn, and recovery when the obstacle clears. |

This is a neural interaction, not a host-language `if obstacle: avoid()` branch.
The host encodes measurements and translates the actual output states to wheels.

## Blocking one candidate action

A left side obstacle excites `SIDE_TURN_RIGHT`. The name describes the direction
away from that obstacle, but this population does not command a turn directly.
It feeds `BLOCK_LIGHT_LEFT`, which inhibits the left light pathway.

The purpose is specific: prevent a light-led left turn toward the side obstacle.
The right light pathway can still operate unless other evidence blocks it.
This demonstrates a contextual restriction on a goal, rather than stopping
all of that goal's possible actions.

## Making a default behavior yield

`FORWARD_RIGHT` excites `SEARCH_RESET`. That reset inhibits the right scene gate
and clears the right wheel output. It forms a feedback loop that can interrupt
right-wheel drive while the left pathway continues to receive scene activity.

Front, side and light activity combine through OR populations into `ANY_GOAL`.
`ANY_GOAL` inhibits `SEARCH_RESET`, with strength 2.5. Inhibiting the reset
reduces its interference with the right motor pathway: this is disinhibition.

Search is not selected by a Python test for all sensors being zero. Its activity
and recovery arise from the connected populations. Check the time course on
Prima-Lux; ACK marks input processing, not a guarantee that every pathway has
settled by that frame.

## A worksheet for your next goal

Before editing the graph, write down:

1. **Desired condition:** what should become true or remain true?
2. **Observations:** which measurements reveal progress or conflict?
3. **Candidate actions:** which movements could help, and in which direction?
4. **Neural evidence:** which sensory and comparison primitives represent support?
5. **Interactions:** which existing actions cooperate, compete, or need a veto?
6. **Action lifetime:** what clears the output, and what allows it to activate again?
7. **Test case:** what setup distinguishes a working interaction from a failure?

For a new goal, decide which relationship you need:

| Relationship | Design decision |
| --- | --- |
| Shared support | Connect compatible evidence to the same candidate action, using operand semantics when the operation requires them. |
| Comparison | Match positive and negative representations and operand units. |
| Competition | Connect incompatible alternatives so their activity can oppose one another. |
| Contextual veto | Identify the exact pathway to suppress and the observation that permits recovery. |
| Default behavior | Define how a goal interrupts the default and how it resumes afterward. |
| Sequence | Define a measured completion condition that enables the next action. |

## Small experiments

Keep a copy of `brain.abdesign.json` outside the project root before editing.
Change one relationship, save the intended design, build, and run. Record your
prediction, sensor conditions, neural populations, wheel states and recovery.

- Remove `FRONT_ANY → BLOCK_LIGHT_RIGHT`. Predict what happens when a front
  obstacle conflicts with right-light approach. Check both wheels, not just a
  single gate population.
- Remove `SIDE_TURN_RIGHT → BLOCK_LIGHT_LEFT`. Does a left side obstacle still
  constrain left-light approach? Which other pathways can affect this trial?
- Remove `ANY_GOAL → SEARCH_RESET`. Does search continue interfering during
  light approach? Restore the connection before testing its strength.
- Remove one direct turn-to-wheel inhibitory connection while retaining its
  turn-to-motor connection. Observe why a bistable output needs its own clear path.
- Add a new measured condition that should suppress search. Choose its
  representation and OR contribution before wiring it into the hierarchy.

A single silent timestep is insufficient to characterize an oscillatory
population. Observe suppression, action and recovery across time and repeated
conditions. Distinguish physical wheel gain from neural operating points.
