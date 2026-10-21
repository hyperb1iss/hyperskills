#!/usr/bin/env bash
# Launch a coding agent on camera inside a throwaway studio, so the take
# shows the agent using the product's demo world and nothing else.
#
# The studio is a fresh project directory (the agent's working directory)
# holding only the copied skills. A separate sandbox directory holds a bin
# dir with only the allowed binaries, empty XDG config, cache, data and state
# dirs, an empty zsh startup dir, and the studio prompt. The agent starts
# under `env -i` with only what auth and the terminal need, plus the demo's
# variables.
#
# Claude Code runs with --permission-mode dontAsk and an explicit tool
# allowlist: allowlisted tools run, everything else is denied without a
# prompt. Never auto or bypass mode (auto mode let a real take escape demo
# mode), and never manual prompts (they stall the take on camera).
# Flags checked against Claude Code 2.1.306 and Codex 0.163.0 --help.

set -u

usage() {
  cat <<'EOF'
Usage: agent-take.sh [options] [-- extra agent arguments]

Agent:
  --agent claude|codex   which CLI to film (default claude)
  --agent-bin PATH       the CLI binary (default: found on PATH; shell
                         functions and aliases are ignored)
  --model NAME           passed as --model (Claude) or -m (Codex)
Studio:
  --dir DIR              the agent's working directory; it shows in the
                         agent's header on camera, so pick a name that reads
                         well (default: a new temp dir). Must be new or empty.
  --skill DIR            copy a skill (a dir with SKILL.md) into the studio;
                         repeatable
  --allow BIN            put BIN on the sandbox PATH; repeatable. Scripts
                         need their interpreter allowed too.
  --env NAME=VALUE       a demo variable, e.g. UNIFI_DEMO_FLEET=1; repeatable
  --pass NAME            pass a variable from this environment; repeatable.
                         Known auth variables pass automatically when set.
  --prompt-file FILE     studio prompt text (default: the built-in one)
Claude Code:
  --tool RULE            allowlisted tool rule, e.g. 'Bash(unifly:*)' or
                         'Skill(unifly)'; repeatable, at least one
Codex:
  --codex-sandbox MODE   read-only (default) or workspace-write
Modes:
  --dry-run              print the exact environment and command; create
                         nothing (secrets in passed variables are masked)
  --prove                build the sandbox (in a fresh temp studio, whatever
                         --dir says) and show the real configuration is
                         unreachable; do not launch
  --probe CMD            for --prove: a command run in the sandbox with the
                         demo variables removed, as an agent escaping demo
                         mode would; repeatable
  --probe-expect REGEX   for --prove: every probe's output must match
  --home DIR             HOME for the take (default: yours, which the agent
                         needs for its login)
  --json                 machine-readable output for --dry-run and --prove
  -h, --help             show this help

Exit codes: 0 ok (or the agent's own exit status after a take), 1 --prove
found a problem, 2 usage error, 3 a binary was not found, 4 the studio or
sandbox could not be built.
EOF
}

die() {
  printf 'agent-take: %s\n' "$2" >&2
  exit "$1"
}

agent=claude
agent_bin=''
model=''
dir=''
prompt_file=''
codex_sandbox=read-only
mode=launch
json=0
home=${HOME:-}
probe_expect=''
skills=()
allows=()
envs=()
passes=()
rules=()
probes=()
extra=()

need() {
  [ $# -ge 2 ] && [ -n "$2" ] || die 2 "$1 needs a value"
}
while [ $# -gt 0 ]; do
  case $1 in
    --agent) need "$@"; agent=$2; shift 2 ;;
    --agent-bin) need "$@"; agent_bin=$2; shift 2 ;;
    --model) need "$@"; model=$2; shift 2 ;;
    --dir) need "$@"; dir=$2; shift 2 ;;
    --skill) need "$@"; skills+=("$2"); shift 2 ;;
    --allow) need "$@"; allows+=("$2"); shift 2 ;;
    --env) need "$@"; envs+=("$2"); shift 2 ;;
    --pass) need "$@"; passes+=("$2"); shift 2 ;;
    --prompt-file) need "$@"; prompt_file=$2; shift 2 ;;
    --tool) need "$@"; rules+=("$2"); shift 2 ;;
    --codex-sandbox) need "$@"; codex_sandbox=$2; shift 2 ;;
    --dry-run) mode=dry-run; shift ;;
    --prove) mode=prove; shift ;;
    --probe) need "$@"; probes+=("$2"); shift 2 ;;
    --probe-expect) need "$@"; probe_expect=$2; shift 2 ;;
    --home) need "$@"; home=$2; shift 2 ;;
    --json) json=1; shift ;;
    -h | --help) usage; exit 0 ;;
    --) shift; extra=("$@"); break ;;
    *) die 2 "unknown option $1 (see --help)" ;;
  esac
done

case $agent in claude | codex) ;; *) die 2 "--agent takes claude or codex" ;; esac
case $codex_sandbox in read-only | workspace-write) ;; *) die 2 "--codex-sandbox takes read-only or workspace-write" ;; esac
[ -n "$home" ] && [ -d "$home" ] || die 2 "HOME is not a directory: ${home:-unset}"
if [ "$agent" = claude ] && [ ${#rules[@]} -eq 0 ]; then
  die 2 "Claude Code takes need at least one --tool rule; dontAsk mode denies everything else"
fi
if [ "$agent" = codex ] && [ ${#rules[@]} -gt 0 ]; then
  die 2 "--tool is a Claude Code allowlist; Codex is limited by --codex-sandbox and PATH instead"
fi

# Variables the launcher owns; a demo variable may not override them.
reserved=' PATH HOME USER LOGNAME TERM COLORTERM TERM_PROGRAM TERM_PROGRAM_VERSION LANG LC_ALL SHELL ZDOTDIR TMPDIR XDG_CONFIG_HOME XDG_CACHE_HOME XDG_DATA_HOME XDG_STATE_HOME CLAUDE_CODE_DISABLE_CLAUDE_MDS CLAUDE_CODE_DISABLE_AUTO_MEMORY BASH_ENV ENV '
valid_name() {
  case $1 in '' | [0-9]* | *[!A-Za-z0-9_]*) return 1 ;; esac
  return 0
}
for pair in ${envs[@]+"${envs[@]}"}; do
  name=${pair%%=*}
  [ "$name" != "$pair" ] || die 2 "--env takes NAME=VALUE, got $pair"
  valid_name "$name" || die 2 "bad variable name in --env $pair"
  case $reserved in *" $name "*) die 2 "--env cannot set $name; the launcher controls it" ;; esac
done
for name in ${passes[@]+"${passes[@]}"}; do
  valid_name "$name" || die 2 "bad variable name for --pass: $name"
  case $reserved in *" $name "*) die 2 "--pass cannot carry $name; the launcher controls it" ;; esac
  eval "isset=\${$name+x}"
  [ -n "$isset" ] || die 2 "--pass $name: the variable is not set here"
done
for skill in ${skills[@]+"${skills[@]}"}; do
  [ -f "$skill/SKILL.md" ] || die 2 "--skill $skill has no SKILL.md"
done
[ -z "$prompt_file" ] || [ -r "$prompt_file" ] || die 2 "cannot read --prompt-file $prompt_file"

resolve_bin() {
  case $1 in
    */*) [ -x "$1" ] && [ ! -d "$1" ] && printf '%s/%s\n' "$(cd "$(dirname "$1")" && pwd -P)" "$(basename "$1")" ;;
    *) type -P "$1" ;;
  esac
}
if [ -z "$agent_bin" ]; then
  agent_bin=$(resolve_bin "$agent") || die 3 "$agent not found on PATH; pass --agent-bin"
else
  wanted_bin=$agent_bin
  agent_bin=$(resolve_bin "$wanted_bin") || die 3 "--agent-bin is not an executable: $wanted_bin"
fi
allow_paths=()
allow_names=()
for bin in ${allows[@]+"${allows[@]}"}; do
  found=$(resolve_bin "$bin") || die 3 "--allow $bin: not found"
  allow_paths+=("$found")
  allow_names+=("$(basename "$found")")
done

if [ -n "$prompt_file" ]; then
  prompt=$(cat "$prompt_file")
else
  prompt='This session runs in a demo studio. The working directory and the commands on PATH are the whole environment, and the demo data they show is the system the user is asking about: work with it as it is. Demo mode is intentional. There is no need to disable it or to look for other configuration, credentials, accounts or networks. Use only the commands available on PATH.'
fi

# Paths. A dry run creates nothing, so new directories show as placeholders.
# A proof builds its own temp studio: it does not depend on the studio path,
# and leaving --dir untouched lets the real take use it next.
[ "$mode" = prove ] && dir=''
if [ "$mode" = dry-run ]; then
  project=${dir:-'<new temp dir>'}
  sandbox='<new temp dir>'
else
  if [ -n "$dir" ]; then
    if [ -e "$dir" ]; then
      [ -d "$dir" ] || die 4 "--dir exists and is not a directory: $dir"
      [ -z "$(ls -A "$dir" 2>/dev/null)" ] || die 4 "--dir must be new or empty: $dir"
    fi
    mkdir -p "$dir" || die 4 "cannot create $dir"
    project=$(cd "$dir" && pwd -P)
  else
    project=$(mktemp -d "${TMPDIR:-/tmp}/studio.XXXXXX") || die 4 'cannot create a studio dir'
    project=$(cd "$project" && pwd -P)
  fi
  sandbox=$(mktemp -d "${TMPDIR:-/tmp}/studio-sandbox.XXXXXX") || die 4 'cannot create a sandbox dir'
  sandbox=$(cd "$sandbox" && pwd -P)
  mkdir -p "$sandbox/bin" "$sandbox/xdg/config" "$sandbox/xdg/cache" "$sandbox/xdg/data" \
    "$sandbox/xdg/state" "$sandbox/zdotdir" "$sandbox/tmp" || die 4 'cannot build the sandbox'
  : >"$sandbox/zdotdir/.zshenv"
  : >"$sandbox/zdotdir/.zshrc"
  i=0
  while [ $i -lt ${#allow_paths[@]} ]; do
    ln -s "${allow_paths[$i]}" "$sandbox/bin/${allow_names[$i]}" || die 4 "cannot link ${allow_paths[$i]}"
    i=$((i + 1))
  done
  if [ "$agent" = claude ]; then skill_root="$project/.claude/skills"; else skill_root="$project/.agents/skills"; fi
  for skill in ${skills[@]+"${skills[@]}"}; do
    mkdir -p "$skill_root" && cp -R "$skill" "$skill_root/$(basename "$skill")" || die 4 "cannot copy skill $skill"
  done
  printf '%s\n' "$prompt" >"$sandbox/studio-prompt.txt"
  # Codex reads project instructions from AGENTS.md in its working root.
  [ "$agent" = codex ] && printf '%s\n' "$prompt" >"$project/AGENTS.md"
fi

shell=/bin/bash
[ -x /bin/zsh ] && shell=/bin/zsh

# The take's environment, as NAME=VALUE words for env -i.
base_env=(
  "HOME=$home"
  "USER=${USER:-$(id -un)}"
  "LOGNAME=${LOGNAME:-${USER:-$(id -un)}}"
  "TERM=${TERM:-xterm-256color}"
  "LANG=${LANG:-en_US.UTF-8}"
  "PATH=$sandbox/bin"
  "SHELL=$shell"
  "ZDOTDIR=$sandbox/zdotdir"
  "TMPDIR=$sandbox/tmp"
  "XDG_CONFIG_HOME=$sandbox/xdg/config"
  "XDG_CACHE_HOME=$sandbox/xdg/cache"
  "XDG_DATA_HOME=$sandbox/xdg/data"
  "XDG_STATE_HOME=$sandbox/xdg/state"
)
for name in COLORTERM TERM_PROGRAM TERM_PROGRAM_VERSION LC_ALL; do
  eval "value=\${$name-}"
  [ -n "$value" ] && base_env+=("$name=$value")
done
if [ "$agent" = claude ]; then
  base_env+=(CLAUDE_CODE_DISABLE_CLAUDE_MDS=1 CLAUDE_CODE_DISABLE_AUTO_MEMORY=1)
  auth_names='ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL CLAUDE_CONFIG_DIR'
else
  auth_names='OPENAI_API_KEY OPENAI_BASE_URL CODEX_HOME'
fi
pass_env=()
for name in $auth_names ${passes[@]+"${passes[@]}"}; do
  eval "isset=\${$name+x}"
  [ -n "$isset" ] || continue
  eval "value=\${$name}"
  pass_env+=("$name=$value")
done
take_env=("${base_env[@]}" ${pass_env[@]+"${pass_env[@]}"} ${envs[@]+"${envs[@]}"})
probe_env=("${base_env[@]}" ${pass_env[@]+"${pass_env[@]}"})

argv=("$agent_bin")
if [ "$agent" = claude ]; then
  tool_names=''
  for rule in "${rules[@]}"; do
    tool=${rule%%(*}
    case ",$tool_names," in *",$tool,"*) ;; *) tool_names="${tool_names:+$tool_names,}$tool" ;; esac
  done
  argv+=(--setting-sources project,local --strict-mcp-config --permission-mode dontAsk
    --tools "$tool_names" --allowedTools "${rules[@]}" --append-system-prompt "$prompt")
  [ -n "$model" ] && argv+=(--model "$model")
else
  argv+=(-C "$project" -s "$codex_sandbox" -a never)
  [ -n "$model" ] && argv+=(-m "$model")
fi
argv+=(${extra[@]+"${extra[@]}"})

masked() {
  case ${1%%=*} in
    *KEY* | *TOKEN* | *SECRET* | *PASSWORD*) printf '%s=<redacted>' "${1%%=*}" ;;
    *) printf '%s' "$1" ;;
  esac
}
json_str() {
  local s=$1
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  s=${s//$'\n'/\\n}
  s=${s//$'\t'/\\t}
  printf '"%s"' "$s"
}
json_array() {
  local sep='' item
  printf '['
  for item in "$@"; do printf '%s%s' "$sep" "$(json_str "$item")"; sep=', '; done
  printf ']'
}

notes=(
  "HOME is the real home so the agent can log in; files directly under it (not under XDG dirs) stay readable to allowed binaries."
  "PATH is a soft brake: the agent's shell may add system directories at startup. The Claude tool allowlist, or the Codex sandbox policy, is what stops other commands."
)
if [ "$agent" = codex ]; then
  notes+=("Codex has no per-command allowlist here; in testing its sandbox blocked network access and writes outside the workspace but could read files under HOME. Its user-level instructions under CODEX_HOME still load.")
fi

if [ "$mode" = dry-run ]; then
  if [ "$json" -eq 1 ]; then
    shown=()
    for pair in "${take_env[@]}"; do shown+=("$(masked "$pair")"); done
    printf '{"agent": %s, "bin": %s, "project": %s, "sandbox": %s,\n' \
      "$(json_str "$agent")" "$(json_str "$agent_bin")" "$(json_str "$project")" "$(json_str "$sandbox")"
    printf ' "env": %s,\n' "$(json_array "${shown[@]}")"
    printf ' "argv": %s,\n' "$(json_array "${argv[@]}")"
    printf ' "skills": %s, "allowed": %s, "notes": %s}\n' \
      "$(json_array ${skills[@]+"${skills[@]}"})" "$(json_array ${allow_paths[@]+"${allow_paths[@]}"})" "$(json_array "${notes[@]}")"
  else
    printf 'studio   %s  (the agent'"'"'s working directory)\n' "$project"
    printf 'sandbox  %s\n' "$sandbox"
    for skill in ${skills[@]+"${skills[@]}"}; do printf 'skill    %s\n' "$skill"; done
    i=0
    while [ $i -lt ${#allow_paths[@]} ]; do printf 'allow    %s -> %s\n' "${allow_names[$i]}" "${allow_paths[$i]}"; i=$((i + 1)); done
    printf '\ncd %q &&\nenv -i \\\n' "$project"
    for pair in "${take_env[@]}"; do printf '  %q \\\n' "$(masked "$pair")"; done
    last=$((${#argv[@]} - 1))
    i=0
    for word in "${argv[@]}"; do
      if [ $i -lt $last ]; then printf '  %q \\\n' "$word"; else printf '  %q\n' "$word"; fi
      i=$((i + 1))
    done
    printf '\n'
    for note in "${notes[@]}"; do printf 'note: %s\n' "$note"; done
  fi
  exit 0
fi

if [ "$mode" = prove ]; then
  results=''
  failed=0
  record() {
    results="$results$1	$2	$3
"
    [ "$2" = ok ] || failed=1
  }
  in_sandbox() {
    # in_sandbox ENV_ARRAY_NAME COMMAND
    local name=$1 command=$2
    eval "set -- \"\${${name}[@]}\""
    (cd "$project" && env -i "$@" /bin/sh -c "$command") 2>&1
  }

  listed=$(ls -A "$sandbox/bin" | sort | tr '\n' ' ')
  wanted=$(printf '%s\n' ${allow_names[@]+"${allow_names[@]}"} | sed '/^$/d' | sort | tr '\n' ' ')
  if [ "$listed" = "$wanted" ]; then record path ok "PATH holds only: ${listed:-nothing}"
  else record path fail "PATH holds $listed; expected $wanted"; fi

  escaped=''
  for tool in curl wget ssh scp nc cat env python3 python node perl ruby git sh bash zsh sudo open xdg-open security; do
    case " ${allow_names[*]-} " in *" $tool "*) continue ;; esac
    if in_sandbox take_env "command -v $tool" >/dev/null; then escaped="$escaped $tool"; fi
  done
  if [ -z "$escaped" ]; then record tools ok 'no shell, network, or file tool resolves unless allowed'
  else record tools fail "resolvable without being allowed:$escaped"; fi

  DEMO_REEL_CANARY=leaked
  export DEMO_REEL_CANARY
  seen=$(in_sandbox take_env /usr/bin/env | sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' | sort | tr '\n' ' ')
  expected=$(for pair in "${take_env[@]}"; do printf '%s\n' "${pair%%=*}"; done | sort | tr '\n' ' ')
  # /bin/sh may add PWD, SHLVL and _ on its own. (A function, because bash
  # 3.2 cannot parse a case statement inside a command substitution.)
  unexpected_names() {
    local n
    for n in $seen; do
      case " $expected PWD SHLVL _ OLDPWD " in
        *" $n "*) ;;
        *) printf ' %s' "$n" ;;
      esac
    done
  }
  extra_names=$(unexpected_names)
  if [ -z "$extra_names" ]; then record env ok 'only the listed variables reach the take'
  else record env fail "unexpected variables reach the take:$extra_names"; fi

  dirty=''
  for d in config cache data state; do
    [ -z "$(ls -A "$sandbox/xdg/$d")" ] || dirty="$dirty $d"
  done
  if [ -z "$dirty" ]; then record xdg ok 'XDG config, cache, data and state dirs are empty'
  else record xdg fail "not empty:$dirty"; fi

  probe_rows=''
  for command in ${probes[@]+"${probes[@]}"}; do
    output=$(in_sandbox probe_env "$command")
    status=$?
    verdict=review
    if [ -n "$probe_expect" ]; then
      if printf '%s' "$output" | grep -Eq -- "$probe_expect"; then verdict=ok; else verdict=fail; failed=1; fi
    fi
    probe_rows="$probe_rows$command	$status	$verdict	$(printf '%s' "$output" | tr '\n\t' '  ' | cut -c1-400)
"
  done

  if [ "$json" -eq 1 ]; then
    if [ "$failed" -eq 0 ]; then ok=true; else ok=false; fi
    printf '{"ok": %s, "project": %s, "sandbox": %s, "checks": [' "$ok" "$(json_str "$project")" "$(json_str "$sandbox")"
    sep=''
    while IFS="	" read -r name status detail; do
      [ -n "$name" ] || continue
      printf '%s{"name": %s, "ok": %s, "detail": %s}' "$sep" "$(json_str "$name")" \
        "$([ "$status" = ok ] && printf true || printf false)" "$(json_str "$detail")"
      sep=', '
    done <<EOF
$results
EOF
    printf '], "probes": ['
    sep=''
    while IFS="	" read -r command status verdict output; do
      [ -n "$command" ] || continue
      printf '%s{"command": %s, "exit": %s, "status": %s, "output": %s}' "$sep" "$(json_str "$command")" \
        "$status" "$(json_str "$verdict")" "$(json_str "$output")"
      sep=', '
    done <<EOF
$probe_rows
EOF
    printf '], "notes": %s}\n' "$(json_array "${notes[@]}")"
  else
    printf '%s' "$results" | awk -F'\t' 'NF >= 2 { printf "%-4s %-6s %s\n", ($2 == "ok" ? "ok" : "FAIL"), $1, $3 }'
    printf '%s' "$probe_rows" | awk -F'\t' 'NF >= 3 {
      mark = ($3 == "ok") ? "ok" : (($3 == "fail") ? "FAIL" : "look")
      printf "%-4s probe  %s (exit %s)\n       %s\n", mark, $1, $2, $4 }'
    for note in "${notes[@]}"; do printf 'note: %s\n' "$note"; done
    printf 'studio %s, sandbox %s\n' "$project" "$sandbox"
    if [ "$failed" -eq 0 ]; then printf 'sandbox holds\n'; else printf 'sandbox leaks\n'; fi
  fi
  exit "$failed"
fi

# Launch. Run the agent as a child, never with exec: an exec'd take that
# exits closes the terminal window the camera is filming.
(cd "$project" && env -i "${take_env[@]}" "${argv[@]}")
status=$?
{
  printf '\nagent-take: take ended (exit %s)\n' "$status"
  printf '  studio  %s\n  sandbox %s\n' "$project" "$sandbox"
  if [ "$agent" = claude ]; then
    printf '  Claude Code keeps the transcript under ~/.claude/projects/ in a directory named after the studio path.\n'
  else
    printf '  Codex keeps session logs under its CODEX_HOME sessions directory.\n'
  fi
  printf '  Read the transcript for anything real before sharing; delete it and both dirs when done.\n'
} >&2
exit "$status"
