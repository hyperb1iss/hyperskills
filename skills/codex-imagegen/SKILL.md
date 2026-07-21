---
name: codex-imagegen
description: Use this skill when an agent must generate or edit raster images through Codex, especially from Claude Code or another harness without native image generation. Activates on mentions of generate image with Codex, delegate image generation, Codex imagegen, make an image, edit this image, multiple images, batch image generation, image variant, visual asset, sprite, mockup, or banner.
---

# Codex Image Generation

Delegate raster image generation and editing to Codex's built-in `$imagegen`
capability, then return a verified workspace artifact to the leader harness.

**Core insight:** instrument Codex, not the desktop window. An authenticated
`codex exec` session can use built-in image generation headlessly. The desktop
app does not need to be open, GUI automation adds no useful capability, and the
shared filesystem is the artifact handoff.

As of Jul 2026, this path is verified with `codex-cli 0.144.6`. CLI and tool
availability are volatile; the installed CLI and a live invocation outrank this
snapshot.

## Select the Execution Route

| Host state                                                                       | Route                                                                                        |
| -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Codex with a callable built-in image-generation tool                             | Invoke `$imagegen` directly. Never launch a child Codex from Codex.                          |
| Claude Code, Pi, Cursor, or another shell-capable harness with `codex` installed | Use `codex exec`. This is the default delegation path.                                       |
| The leader already has Codex MCP tools named `codex` and `codex-reply`           | Use MCP when iterative art direction benefits from a persistent thread.                      |
| No native tool, Codex CLI, or configured Codex MCP server                        | Stop with the missing prerequisite and the exact error. Do not substitute another generator. |

Run `codex --version` before the first delegated call. Respect the user's Codex
configuration; never set `--model`, `-m`, or `-c model=`. Authentication,
entitlements, workspace policy, and image-generation availability belong to the
installed Codex environment.

Use the user's normal Codex session configuration. This skill bundles no Codex
agent profile and requires no model or reasoning override.

Do not start or automate the ChatGPT desktop app. Do not install an MCP server,
change Claude configuration, or switch to API billing unless the user asks.

## Establish the Artifact Contract

Resolve these inputs before launching Codex:

| Input                | Rule                                                                                                                                                  |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Intent               | Classify as new generation, edit, refinement, or variants.                                                                                            |
| Destination          | Honor the user's path. Otherwise follow the repo's existing asset layout, or use `assets/generated/<descriptive-slug>.png` when no convention exists. |
| Existing destination | Create a sibling version such as `hero-v2.png`; overwrite only when explicitly requested.                                                             |
| Input images         | Label every image as edit target, content reference, style reference, or compositing input.                                                           |
| Exact text           | Quote verbatim, preserve capitalization, and forbid any other text unless requested.                                                                  |
| Invariants           | For edits, state what may change and what must remain unchanged.                                                                                      |
| Avoid list           | Carry the user's negative constraints without adding invented brand, narrative, or stylistic requirements.                                            |

Resolve relative paths against the leader's current workspace. Keep the final
asset inside that workspace. Built-in generation may initially save under
`$CODEX_HOME`; that location is staging, not a valid final destination for a
project asset.

## Delegate with `codex exec`

Use a single-quoted heredoc so prompts containing backticks, `$()`, quotes, or
shell metacharacters remain data. Before executing, confirm `IMAGEGEN_BRIEF`
does not appear as an exact standalone line in inserted content; if it does,
choose a different quoted delimiter and update both marker lines. Omit `-i`
when there are no input images.

```bash
codex exec \
  --ephemeral \
  --sandbox workspace-write \
  -C "$PWD" \
  -i "/absolute/path/to/reference.png" \
  - <<'IMAGEGEN_BRIEF'
$imagegen

Create or edit the requested raster asset.

Intent: <generation | edit | refinement | variant>
Asset purpose: <where and how the image will be used>
Primary request: <the user's request, preserving their specificity>
Input images:
- Image 1: <edit target | content reference | style reference | compositing input>
Destination: <workspace-relative or absolute workspace path>
Text (verbatim): "<exact text, or none>"
Must preserve: <edit invariants, or none>
Constraints: <required properties>
Avoid: <negative constraints>

Execution requirements:
- Use the built-in image-generation tool. Do not substitute SVG, HTML, CSS,
  canvas, stock imagery, or a hand-authored placeholder.
- Do not switch to an Images API script, another model path, or paid API
  fallback.
- Inspect the generated result visually. Check subject, composition, text,
  constraints, and edit invariants.
- If one focused correction is clearly necessary, make that correction and
  inspect again. Do not wander through speculative variants.
- Move or copy the selected final into Destination. Do not leave the only copy
  under CODEX_HOME.
- Do not overwrite an existing destination unless the brief explicitly allows
  replacement.

Return this receipt:
STATUS: complete | blocked
MODE: built-in-imagegen
FILES:
- <absolute final path>
FINAL PROMPT: <the prompt actually used>
VERIFICATION:
- <what was visually checked>
NOTES: <material limitations, or none>
IMAGEGEN_BRIEF
```

`codex exec` refuses to launch when `-C` targets a directory outside a trusted
git repository, failing with `Not inside a trusted directory and
--skip-git-repo-check was not specified.` Add `--skip-git-repo-check` only when
the workspace is deliberately not a git repo, such as a scratchpad or temporary
build area. Inside a project repo, omit the flag and keep the trust check.

For multiple input images, add one `-i` argument per file and preserve the same
ordering in the brief. Use absolute paths when the leader and Codex might resolve
working directories differently.

Do not launch a duplicate while `codex exec` is alive. Image generation may
outlast a harness's first yield window; poll the existing process or session.
Treat output growth and process state as liveness signals, not elapsed time.

## Handle Each Image Shape

| Request                  | Execution shape                                                                                                  |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| One new asset            | One `codex exec` call with no image attachment.                                                                  |
| Edit an existing asset   | Attach the edit target with `-i`; repeat preservation invariants in the brief.                                   |
| Refine a generated asset | Attach the prior final as the edit target and request one targeted delta.                                        |
| Several distinct assets  | Launch one delegated call per independent asset concurrently, with isolated prompts, destinations, and receipts. |
| Variants of one concept  | Launch one call per variant concurrently when independent and name destinations deterministically.               |
| Preview-only exploration | Still request a concrete workspace path so the leader can inspect and present the artifact.                      |

Do not use one broad batch prompt for unrelated assets. Distinct assets need
distinct prompts; otherwise one failure makes the receipt ambiguous and visual
constraints bleed between outputs.

### Parallel multi-image generation

The built-in tool still performs one image-generation call per asset or variant.
For true multi-image concurrency, fan out independent `codex exec` calls from
the leader harness instead of asking one child session to manage an opaque
batch.

Before launch, assign every job a deterministic destination such as
`concept-01.png`, `concept-02.png`, and `concept-03.png`. Give each process its
own prompt and receipt. Shared reference images may be read by every job; output
paths and temporary receipt paths must never collide.

Use the leader's native parallel tool dispatch when available. Do not hardcode
an arbitrary concurrency cap into the skill; honor the harness and account
capacity already in force. If the host cannot dispatch concurrently, preserve
the same isolated job shape and run it sequentially.

Track completion as `N/total`. On partial failure, keep and report successful
assets, then retry only failed jobs after diagnosing their exact errors. Never
discard a valid sibling or rerun the whole batch to make the reporting look
atomic.

For an edit, use language such as:

```text
Change only the background to a misty violet dawn. Preserve the subject,
silhouette, camera angle, crop, facial identity, clothing, and all foreground
edges. Add no text or watermark.
```

For a refinement, change one dimension at a time. "Keep everything else
unchanged" is load-bearing, not decorative.

## Verify the Handoff

Codex's receipt is a claim until the leader verifies the filesystem artifact.

1. Confirm every reported final path exists inside the workspace.
2. Confirm each file is non-empty and `file <path>` identifies the requested
   raster format.
3. Confirm no requested deliverable exists only under `$CODEX_HOME`.
4. Inspect the asset in the leader harness when it has image-viewing support.
   Otherwise report that visual verification was performed by delegated Codex,
   not by the leader.
5. Return the final path, final prompt, generation mode, and verification notes
   to the user. Never reduce the handoff to "done."

`codex exec` may echo the final receipt twice in one output stream, once as
streamed agent output and once as the final message. Duplicate receipt text is
one run, not two; count generations by process invocations.

If Codex generated successfully but failed to move the selected image, use the
exact staging path from its receipt and copy it non-destructively into the
workspace. Never hunt broadly through another user's generated-image history or
guess which file belongs to the run.

If the final path is missing, the format is wrong, or the receipt is malformed,
the task is not complete. Ask the same Codex session for a corrected handoff, or
run one fresh, tightly-scoped call with the failed receipt and exact gap.

## Optional Threaded MCP Route

Use MCP only when the Codex server is already configured or the user explicitly
asks to configure it. A one-time Claude Code setup is:

```bash
claude mcp add --scope user codex -- codex mcp-server
```

The server exposes `codex` to start a session and `codex-reply` to continue it.
Start with the same brief used for `codex exec`, set `cwd` to the shared
workspace, and use `sandbox: workspace-write`. Preserve the returned `threadId`.
Send targeted refinements through `codex-reply`, then verify the resulting files
at the consumption boundary.

MCP improves conversational refinement; it is not more capable than the direct
path. Do not make MCP configuration a prerequisite for one-shot generation.

## Failure and Fallback Policy

| Failure                                                     | Response                                                                                                                             |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `codex` missing                                             | Report that the Codex CLI is required and include the failed command.                                                                |
| Launch fails with `Not inside a trusted directory`          | Add `--skip-git-repo-check` for a deliberately non-git workspace, or point `-C` at the trusted repo.                                 |
| Authentication or entitlement failure                       | Preserve the exact error and ask the user to repair Codex access. Do not retry blindly.                                              |
| `$imagegen` or built-in image tool unavailable              | Report the capability gap. Do not claim the desktop app will fix it.                                                                 |
| Built-in tool fails once                                    | Read the error, correct a specific prompt or input issue, and retry once.                                                            |
| Built-in tool fails again                                   | Stop with the two failure receipts and the remaining blocker.                                                                        |
| User explicitly requests API or large paid batch generation | Hand off to Codex's native image-generation skill or current OpenAI API guidance; state that `OPENAI_API_KEY` and API billing apply. |

Never silently downgrade to a different image model or API path. A fallback that
changes billing, authentication, transparency behavior, or output semantics is a
new user decision.

## Anti-Patterns

| Anti-Pattern                                        | Fix                                                                                    |
| --------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Automating the ChatGPT desktop window               | Use `codex exec` or the configured Codex MCP server.                                   |
| Naming this skill `imagegen`                        | Keep `codex-imagegen`; Codex already owns native `$imagegen`.                          |
| Launching child Codex from a Codex host             | Invoke the built-in tool directly.                                                     |
| Setting a model override                            | Respect the user's Codex configuration.                                                |
| Using the Images API by default                     | Use built-in generation; API billing requires explicit intent.                         |
| Leaving project assets under `$CODEX_HOME`          | Copy the selected final into the workspace and verify it.                              |
| Overwriting the source during an edit               | Write a sibling version unless replacement was explicit.                               |
| Replacing a requested raster asset with SVG or CSS  | Delegate the actual bitmap request to image generation.                                |
| Asking the leader to trust a textual receipt        | Verify the file and inspect it when the host supports images.                          |
| Sending unrelated assets in one prompt              | Run one isolated delegation per asset.                                                 |
| Serializing independent image jobs by default       | Fan out isolated `codex exec` calls through the leader's native parallel dispatch.     |
| Starting another process because generation is slow | Poll the live process; duplicate generations waste quota and create ambiguous outputs. |

## What This Skill is NOT

- Not a generic image-prompt cookbook; Codex's native `$imagegen` skill owns
  detailed prompting and image-tool behavior.
- Not a vector, SVG, icon-system, HTML, CSS, canvas, or deterministic diagram
  workflow.
- Not desktop GUI automation.
- Not permission to incur API charges or change authentication.
- Not a replacement for human art direction or final production review when
  typography, likeness, legal clearance, or brand fidelity is critical.
