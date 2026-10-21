# Build the world the demo needs

A reel needs a world that looks lived in, never touches anyone's real data, and is the same on every take. Build it into the product as a real mode, not as fixtures the camera sees once: the act of building it is itself a test, and later takes, screenshots, docs, and agents all reuse it.

## What a demo world is

| Property                      | What it means                                                                     | Example                                                                                             |
| ----------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Seeded                        | One seed produces the whole world; the same seed gives the same world             | `unifly --demo-fleet`, default seed 2077, with `--demo-seed` to pick another                        |
| Offline                       | No network client is built and no real config, keyring, or account is read        | Unifly's fleet mode never reads its config file or keyring and never constructs an HTTP client      |
| Fictional                     | Invented names and reserved address space, so nothing on screen belongs to anyone | A studio called "Neon Harbor Studios"; RFC 1918, 5737 and 3849 addresses; locally administered MACs |
| Lived in                      | Enough scale and texture to read as real                                          | 3 switches, 9 access points, 142 clients, six VLANs, a week of events, a rogue neighbor network     |
| Scripted trouble              | Something worth diagnosing, so a demo has a story                                 | One AP offline, one mid-upgrade, one with weak signal and an update pending                         |
| Time from a tick, not a clock | Animation and history derive from a seeded generator and a tick counter           | The same seed replays the same chart shapes whenever it is launched                                 |
| Deterministic order           | Lists sort before paging; tables keep the same row order every run                | Unifly sorted store-backed lists and policies by evaluation order before any shot was stable        |
| Pinned clock for exports      | Anything that prints a timestamp uses a fixed demo instant                        | Demo exports pin an observed-at instant, so the same seed exports the same bytes                    |

## Writes inside the world

Decide each write's behavior explicitly:

- **Harmless actions play out.** Restart, locate, power-cycle a port: the demo shows the effect and logs an event.
- **Anything else refuses clearly** ("unavailable in demo mode") before touching configuration.
- **Never fake a success that vanishes.** Each unifly CLI run rebuilt its fleet from the seed, so a port write would have appeared to succeed and then disappeared on the next command. It stays refused.

## Building it is a test

Building a demo world exercises the product's own data paths in a new configuration, so expect it to find bugs that real users hit. Unifly's fleet routed demo records through the real conversion code, and building it found six bugs that affected real controllers: the topology view drew every switch to every AP, the firewall NAT tab was always empty, a chart read millisecond timestamps as seconds, the event backlog replayed out of order, overlapping connect and disconnect could hang, and the documented `UNIFI_DEMO=1` form was rejected. An independent review then found that the Settings screen could escape the fleet and connect to a real controller.

Feed demo records through the same parsers and conversions real data uses. A demo world that bypasses them tests nothing and drifts from the product.

## When the product drives real hardware or live state

Some products cannot be faked: hypercolor drives real RGB devices. Isolate the state instead of the world:

- Run each take against a disposable copy of the active scene, detect writes that escape it, and verify the restore afterwards. Hypercolor's runner exited with its own code on a failed restore, and a later capture pass compared scene hashes before and after each take.
- Benchmark fixes on a second, isolated instance, never the one the camera or the user is watching. Hypercolor's A/B daemon ran in its own user and network namespace with every device driver disabled and its state on a real disk.
- Keep the engine in the loop when rendering offline: hypercolor's reel fed its score through the engine's own audio analyzer and drew LED positions from the engine's own spatial layout, so composed shots still showed real behavior.

## Web apps

- Seed the database from a fixture the repo owns, and reset it before each take.
- Sign in as a persona whose name is fine on camera; crop or hide any account footer (hypercolor cropped every UI pane above the sidebar footer that showed the account name).
- Fix the viewport, locale, timezone, and color scheme. Freeze time with the capture script's clock ([capture.md](capture.md)) so relative dates ("3 minutes ago") and animations repeat.
- Wait for real readiness signals (data rendered, chart filled), never a fixed sleep, and record which signal the shot waited on.

## Keep the agent inside the world

A demo mode is a convention the product honors, not a wall. An agent filmed using the product can step outside it, and a careful agent may decide it should. Unifly's first agent take ran `env -u UNIFI_DEMO_FLEET`, read the real config, and made a read-only call to a real controller, reasoning that "a punch list from it would be fiction". The fix was to make the demo world the only world reachable: an empty XDG config, a PATH with only the product, a tool allowlist, and a studio prompt that says the demo is the environment. [agent-on-camera.md](agent-on-camera.md) and `scripts/agent-take.sh` cover the setup and the proof.

Tell agents in the product's own skill or docs that demo data is fictional, so they never present it as the user's real system outside the studio.

## Check the world before shooting

- Two launches with the same seed produce the same output (byte for byte for CLI output and exports; frame for frame, or within a stated pixel tolerance, for UI).
- Nothing on screen resolves to a real person, customer, hostname, or address.
- Every write either plays out harmlessly or refuses clearly.
- The scripted trouble is there and findable from the product's normal surfaces.
