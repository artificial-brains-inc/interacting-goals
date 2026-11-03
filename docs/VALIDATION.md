# Validation

## Local checks

After installation:

```bash
python -m unittest discover -s tests -v
```

Checks cover the saved public graph, goal-interaction topology, operating points,
operand units, sensor/device mapping, wheel decoding, ACK ordering, stale/missing
ACK handling, stop/save cleanup, pip-less environment repair, and the actual
SDK command dispatch with device calls mocked.

A topology fingerprint covers all 69 non-transport relationships. A separate
world fingerprint checks that course, robot, sensor settings and light geometry
match the included world.

These checks do not compile on a live Prima-Lux, execute its neural dynamics,
or render and simulate the world in Webots. Record those results separately.
A successful public-design validation is not a live behavior test.

## Device and simulation checks

Run the standard design, build and run commands from the README. Preserve the
supplied design and configuration for the initial run. In the SDK's telemetry view,
inspect the named populations alongside the physical robot and run logs.

| Trial | Check |
| --- | --- |
| Startup | Correct obstacle/light arena, named brain installed, stream and fresh ACKs present |
| Free-space light approach | Left/right light evidence produces the corresponding physical turn |
| Front obstacle during approach | Front turn activity, both light gates, appropriate wheel suppression and recovery |
| Same-side light and side obstacle | The corresponding light pathway is blocked; side populations have no direct motor control |
| Light blackout | Search reset activity when other sensory goals are quiet, then interruption when evidence returns |
| Similar left/right evidence | Observe competition and possible stalls; do not assume a guaranteed winner |
| Timing | ACK and decision steps match; each acknowledged output precedes exactly one configured movement interval |
| Close Webots | Launcher prints Stop/save confirmation and device reports idle STOPPED |
| Ctrl+C | Run exits through cleanup, motors zero where controller remains available, Stop/save confirmed |

When judging an interaction, observe activity over time. A connection intended
as a veto must be checked for both suppression and recovery. The default SDK
reference does not guarantee a precise percentage of suppression.

## Record a useful result

Keep the saved design, `config.json`, initial robot pose, stimulus seed if used,
and whether neural dynamics were reset. Save `logs/run-*.jsonl`,
`logs/sensors-*.jsonl` and `logs/launcher_state.json`. Keep `.env` and API keys out
of shared records. Compare one design change at a time.
