# Build the world the demo needs

A reel needs a world that looks lived in, never touches anyone's real data, and is the same on every take. Build it into the product as a real mode, not as fixtures the camera sees once: the act of building it is itself a test, and later takes, screenshots, docs, and agents all reuse it.

## What a demo world is

| Property                      | What it means                                                                     | Example                                                                                              |
| ----------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Seeded                        | One seed produces the whole world; the same seed gives the same world             | `acme --demo`, or `ACME_DEMO=1`, with `--demo-seed` to pick another world                            |
| Offline                       | No network client is built and no real config, keyring, or account is read        | Demo mode returns before the code that loads config or opens a connection                            |
| Fictional                     | Invented names and reserved address space, so nothing on screen belongs to anyone | An invented company; RFC 1918, 5737 and 3849 addresses; example.com names; locally administered MACs |
| Lived in                      | Enough scale and texture to read as real                                          | Dozens of devices or records, a week of history, a few odd neighbors                                 |
| Scripted trouble              | Something worth diagnosing, so a demo has a story                                 | One device offline, one mid-upgrade, one with a pending update and weak signal                       |
| Time from a tick, not a clock | Animation and history derive from a seeded generator and a tick counter           | The same seed replays the same chart shapes whenever it is launched                                  |
| Deterministic order           | Lists sort before paging; tables keep the same row order every run                | Sort store-backed lists before paging; list rules in evaluation order                                |
| Pinned clock for exports      | Anything that prints a timestamp uses a fixed demo instant                        | Demo exports pin an observed-at instant, so the same seed exports the same bytes                     |

## Writes inside the world

Decide each write's behavior explicitly:

- **Harmless actions play out.** Restart, locate, power-cycle: the demo shows the effect and logs an event.
- **Anything else refuses clearly** ("unavailable in demo mode") before touching configuration.
- **Never fake a success that vanishes.** When each run rebuilds the world from its seed, a write appears to succeed and then disappears on the next command. Refuse it instead.

## Building it is a test

Building a demo world exercises the product's own data paths in a new configuration, so expect it to find bugs that real users hit: views that draw wrong relationships, tabs that never receive their data, timestamps read in the wrong unit, events replayed out of order, a documented flag the parser rejects. Have someone else review the demo mode too; a screen that can switch the product back to a real account is an escape hatch.

Feed demo records through the same parsers and conversions real data uses. A demo world that bypasses them tests nothing and drifts from the product. [examples.md](examples.md) has one demo world that found six real bugs before a frame was shot.

## When the product drives real hardware or live state

Some products cannot be faked, such as a daemon driving physical devices. Isolate the state instead of the world:

- Run each take against a disposable copy of the active state, detect writes that escape it, and verify the restore afterwards (for example, hash the state before and after each take and fail the run on a mismatch).
- Benchmark fixes on a second, isolated instance, never the one the camera or the user is watching: its own namespaces, device drivers off, and state on a real disk.
- Keep the engine in the loop when rendering offline: feed recorded inputs through the product's own analysis code and draw from its own layout data, so composed shots still show real behavior.

## Web apps

- Seed the database from a fixture the repo owns, and reset it before each take.
- Sign in as a persona whose name is fine on camera; crop or hide any account footer that shows a real name.
- Fix the viewport, locale, timezone, and color scheme. Freeze time with the capture script's clock ([capture.md](capture.md)) so relative dates ("3 minutes ago") and animations repeat.
- Wait for real readiness signals (data rendered, chart filled), never a fixed sleep, and record which signal the shot waited on.

## Keep the agent inside the world

A demo mode is a convention the product honors, not a wall. An agent filmed using the product can step outside it, and a careful agent may decide it should: unset the demo variable, read the real configuration, and call the real service, because a report from demo data "would be fiction". Make the demo world the only world easily reachable: a throwaway HOME, empty XDG dirs, a PATH with only the product, a tool allowlist, and a studio prompt that says the demo is the environment. [agent-on-camera.md](agent-on-camera.md) and `scripts/agent-take.sh` cover the setup and what its proof does and does not establish.

Tell agents in the product's own skill or docs that demo data is fictional, so they never present it as the user's real system outside the studio.

## Check the world before shooting

- Two launches with the same seed produce the same output (byte for byte for CLI output and exports; frame for frame, or within a stated pixel tolerance, for UI).
- Nothing on screen resolves to a real person, customer, hostname, or address.
- Every write either plays out harmlessly or refuses clearly.
- The scripted trouble is there and findable from the product's normal surfaces.
