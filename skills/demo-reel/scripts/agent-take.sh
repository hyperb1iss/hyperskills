#!/usr/bin/env bash
# Launch a coding agent on camera inside a throwaway studio, so the take
# shows the agent using the product's demo world.
#
# The studio is a fresh project directory (the agent's working directory)
# holding only the copied skills and, for Claude Code, a project settings
# file. A separate sandbox directory holds a throwaway HOME, a bin dir with
# only the allowed binaries, empty XDG config, cache, data and state dirs,
# an empty zsh startup dir, and the studio prompt. The agent signs in from a
# dedicated config dir (CLAUDE_CONFIG_DIR or CODEX_HOME), set up once with
# --login, so the user's real HOME and agent config stay out of the take.
# Both directories are deleted when the script exits unless --keep is given.
#
# Claude Code runs in dontAsk mode with an explicit allowlist, written to the
# studio's .claude/settings.json and also passed with --settings: allowlisted
# tools run, everything else is denied without a prompt, auto and bypass
# modes are disabled, and file reads outside the studio are blocked. Never
# auto or bypass mode, never manual prompts on camera.
#
# This is a set of brakes, not isolation: env -i does not stop a command
# from running a system binary by absolute path, and the OS keychain is
# reached by user identity, not HOME. --prove shows what holds.
# Flags and settings keys checked against Claude Code 2.1.306 and Codex
# 0.163.0 (--help output and the Claude binary's settings schema).

set -u

usage() {
  cat <<'EOF'
Usage: agent-take.sh [options] [-- extra agent arguments]

Agent:
  --agent claude|codex   which CLI to film (default claude)
  --agent-bin PATH       the CLI binary (default: found on PATH; shell
                         functions and aliases are ignored). A script with a
                         #! line runs through its interpreter's absolute
                         path; the interpreter never joins the take's PATH.
  --model NAME           passed as --model (Claude) or -m (Codex)
  --agent-config DIR     the agent's dedicated config and login dir (default
                         ~/.local/state/demo-reel/claude or .../codex, under
                         XDG_STATE_HOME when set)
  --login                sign the agent in inside --agent-config, then exit
                         (once per machine, before filming)
  --real-home            run the take with your real HOME and the agent's
                         normal config. Not recommended: anything under HOME
                         is then reachable.
Studio:
  --dir DIR              the agent's working directory; it shows in the
                         agent's header on camera, so pick a name that reads
                         well (default: a new temp dir). Must be new or empty.
  --skill DIR            copy a skill (a dir with SKILL.md) into the studio;
                         repeatable. Links that resolve outside it are refused.
  --allow BIN            put BIN on the sandbox PATH; repeatable. A script
                         that runs through env needs its interpreter allowed.
  --env NAME=VALUE       a demo variable, e.g. ACME_DEMO=1; repeatable
  --pass NAME            pass a variable from this environment; repeatable.
                         API key variables pass automatically when set.
  --prompt-file FILE     studio prompt text (default: the built-in one)
  --keep                 keep the studio and sandbox dirs after exit
Claude Code:
  --tool RULE            allowlisted tool rule, e.g. 'Bash(acme:*)' or
                         'Skill(acme)'; repeatable, at least one
Codex:
  --codex-sandbox MODE   read-only (default) or workspace-write. The sandbox
                         is preflighted; there is no fallback to full access.
Modes:
  --dry-run              print the exact environment, command and settings;
                         create nothing (API keys are masked)
  --prove                build the sandbox in a fresh temp studio, check what
                         the take can reach, run the probes, then clean up
  --probe CMD            for --prove: a command run in the sandbox with the
                         demo variables removed; repeatable
  --probe-expect REGEX   for --prove: every probe's output must match
  --json                 machine-readable output for --dry-run and --prove
  -h, --help             show this help

Exit codes: 0 ok (or the agent's own exit status after a take), 1 --prove
found a problem, 2 usage error, 3 a binary, interpreter, login dir, or the
Codex sandbox is unavailable, 4 the studio or sandbox could not be built.
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
keep=0
real_home=0
agent_config=''
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
    --agent-config) need "$@"; agent_config=$2; shift 2 ;;
    --login) mode=login; shift ;;
    --real-home) real_home=1; shift ;;
    --dir) need "$@"; dir=$2; shift 2 ;;
    --skill) need "$@"; skills+=("$2"); shift 2 ;;
    --allow) need "$@"; allows+=("$2"); shift 2 ;;
    --env) need "$@"; envs+=("$2"); shift 2 ;;
    --pass) need "$@"; passes+=("$2"); shift 2 ;;
    --prompt-file) need "$@"; prompt_file=$2; shift 2 ;;
    --keep) keep=1; shift ;;
    --tool) need "$@"; rules+=("$2"); shift 2 ;;
    --codex-sandbox) need "$@"; codex_sandbox=$2; shift 2 ;;
    --dry-run) mode=dry-run; shift ;;
    --prove) mode=prove; shift ;;
    --probe) need "$@"; probes+=("$2"); shift 2 ;;
    --probe-expect) need "$@"; probe_expect=$2; shift 2 ;;
    --json) json=1; shift ;;
    -h | --help) usage; exit 0 ;;
    --) shift; extra=("$@"); break ;;
    *) die 2 "unknown option $1 (see --help)" ;;
  esac
done

case $agent in claude | codex) ;; *) die 2 "--agent takes claude or codex" ;; esac
case $codex_sandbox in read-only | workspace-write) ;; *) die 2 "--codex-sandbox takes read-only or workspace-write" ;; esac
[ -n "${HOME:-}" ] && [ -d "$HOME" ] || die 2 "HOME is not a directory: ${HOME:-unset}"
if [ "$mode" != login ] && [ "$agent" = claude ] && [ ${#rules[@]} -eq 0 ]; then
  die 2 "Claude Code takes need at least one --tool rule; dontAsk mode denies everything else"
fi
if [ "$agent" = codex ] && [ ${#rules[@]} -gt 0 ]; then
  die 2 "--tool is a Claude Code allowlist; Codex is limited by --codex-sandbox and PATH instead"
fi

# JSON string escaping for every control character, built once.
ctl_chars=()
ctl_escapes=()
for code in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31; do
  ctl_chars+=("$(printf "\\$(printf '%03o' "$code")")")
  ctl_escapes+=("$(printf '\\u%04x' "$code")")
done
# A command substitution strips a trailing newline, so set that one directly.
ctl_chars[9]=$'\n'
json_str() {
  local s=$1 i=0
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  while [ $i -lt 31 ]; do
    s=${s//"${ctl_chars[$i]}"/${ctl_escapes[$i]}}
    i=$((i + 1))
  done
  printf '"%s"' "$s"
}
json_array() {
  local sep='' item
  printf '['
  for item in "$@"; do printf '%s%s' "$sep" "$(json_str "$item")"; sep=', '; done
  printf ']'
}

# Variables the launcher owns; a demo variable may not override them.
reserved=' PATH HOME USER LOGNAME TERM COLORTERM TERM_PROGRAM TERM_PROGRAM_VERSION LANG LC_ALL SHELL ZDOTDIR TMPDIR XDG_CONFIG_HOME XDG_CACHE_HOME XDG_DATA_HOME XDG_STATE_HOME CLAUDE_CONFIG_DIR CODEX_HOME CLAUDE_CODE_DISABLE_CLAUDE_MDS CLAUDE_CODE_DISABLE_AUTO_MEMORY BASH_ENV ENV '
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
[ -z "$prompt_file" ] || [ -r "$prompt_file" ] || die 2 "cannot read --prompt-file $prompt_file"

real_path() {
  # real_path PATH -> absolute path with every symlink resolved
  if command -v realpath >/dev/null 2>&1; then realpath "$1" 2>/dev/null
  elif [ -d "$1" ]; then (cd "$1" && pwd -P)
  else
    local target=$1 n=0
    while [ -L "$target" ] && [ $n -lt 40 ]; do
      local link
      link=$(readlink "$target")
      case $link in /*) target=$link ;; *) target="$(dirname "$target")/$link" ;; esac
      n=$((n + 1))
    done
    [ -e "$target" ] || return 1
    printf '%s/%s\n' "$(cd "$(dirname "$target")" && pwd -P)" "$(basename "$target")"
  fi
}
# A skill may hold links, but every one must resolve inside the skill.
for skill in ${skills[@]+"${skills[@]}"}; do
  [ -f "$skill/SKILL.md" ] || die 2 "--skill $skill has no SKILL.md"
  root=$(real_path "$skill") || die 2 "cannot resolve --skill $skill"
  while IFS= read -r link; do
    [ -n "$link" ] || continue
    target=$(real_path "$link") || die 2 "--skill $skill has a broken link: $link"
    case $target/ in "$root"/*) ;; *) die 2 "--skill $skill has a link that leaves the skill: $link -> $target" ;; esac
  done <<EOF
$(find "$skill" -type l 2>/dev/null)
EOF
done

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

# shebang_of FILE -> the #! line's words, or nothing for a native binary.
shebang_of() {
  [ "$(head -c 2 "$1" 2>/dev/null)" = '#!' ] || return 1
  head -n 1 "$1" | sed 's/^#![[:space:]]*//'
}
# An npm-installed agent is a script that starts with #!/usr/bin/env node.
# Under the take's PATH, env would not find node, so run the interpreter by
# its absolute path. It never joins PATH.
launch=()
interpreter=''
if line=$(shebang_of "$agent_bin"); then
  set -f
  set -- $line
  set +f
  [ $# -gt 0 ] || die 3 "$agent_bin has an empty #! line"
  if [ "$(basename "$1")" = env ]; then
    shift
    [ "${1:-}" = -S ] && shift
    [ $# -gt 0 ] || die 3 "$agent_bin runs through env without naming an interpreter"
    interpreter=$(type -P "$1") || die 3 "$agent_bin needs $1, which is not on this PATH; install it or pass --agent-bin to a native binary"
    shift
  else
    interpreter=$1
    shift
    [ -x "$interpreter" ] || die 3 "$agent_bin needs $interpreter, which is not executable"
  fi
  launch=("$interpreter" "$@" "$agent_bin")
else
  launch=("$agent_bin")
fi

allow_paths=()
allow_names=()
for bin in ${allows[@]+"${allows[@]}"}; do
  found=$(resolve_bin "$bin") || die 3 "--allow $bin: not found"
  allow_paths+=("$found")
  allow_names+=("$(basename "$found")")
done

[ -n "$agent_config" ] || agent_config="${XDG_STATE_HOME:-$HOME/.local/state}/demo-reel/$agent"
case $agent_config in /*) ;; *) agent_config="$(pwd -P)/$agent_config" ;; esac
# The login dir gets a trust entry written into its .claude.json, so it must
# never be the operator's own config.
real_cfg=$agent_config
while [ "$real_cfg" != / ] && [ "${real_cfg%/}" != "$real_cfg" ]; do real_cfg=${real_cfg%/}; done
[ -d "$real_cfg" ] && real_cfg=$(cd "$real_cfg" && pwd -P)
real_home_dir=$(cd "$HOME" && pwd -P)
for own in "$real_home_dir" "$real_home_dir/.claude" "$real_home_dir/.codex" /; do
  [ "$real_cfg" = "$own" ] && die 2 "--agent-config $agent_config is the operator's own config; pick a dedicated dir"
done
config_var=CLAUDE_CONFIG_DIR
[ "$agent" = codex ] && config_var=CODEX_HOME

if [ "$mode" = login ]; then
  mkdir -p "$agent_config" && chmod 700 "$agent_config" || die 3 "cannot create $agent_config"
  printf 'agent-take: signing %s in with %s=%s\n' "$agent" "$config_var" "$agent_config" >&2
  if [ "$agent" = claude ]; then
    env "$config_var=$agent_config" "${launch[@]}" auth login
  else
    env "$config_var=$agent_config" "${launch[@]}" login
  fi
  exit $?
fi
if [ "$real_home" -eq 0 ] && [ "$mode" = launch ] && [ ! -d "$agent_config" ]; then
  die 3 "no agent login dir at $agent_config; run agent-take.sh --agent $agent --login first (or pass --agent-config)"
fi

if [ -n "$prompt_file" ]; then
  prompt=$(cat "$prompt_file")
else
  prompt='This session runs in a demo studio. The working directory and the commands on PATH are the whole environment, and the demo data they show is the system the user is asking about: work with it as it is. Demo mode is intentional. There is no need to disable it or to look for other configuration, credentials, accounts or networks. Use only the commands available on PATH.'
fi

# Claude Code settings: written to the studio and passed with --settings.
# Key names and value types come from the 2.1.306 binary's settings schema;
# a misspelled key would be ignored silently.
settings_json() {
  local sep='' rule
  printf '{\n  "permissions": {\n    "defaultMode": "dontAsk",\n    "allow": ['
  for rule in "${rules[@]}"; do printf '%s%s' "$sep" "$(json_str "$rule")"; sep=', '; done
  printf '],\n    "deny": ["WebFetch", "WebSearch"],\n'
  printf '    "blockReadsOutsideWorkingDirectories": true,\n'
  printf '    "disableBypassPermissionsMode": "disable",\n'
  printf '    "disableAutoMode": "disable"\n  },\n'
  printf '  "disableAutoMode": "disable"\n}\n'
}

# Paths. A dry run creates nothing, so new directories show as placeholders.
# A proof builds its own temp studio and leaves --dir for the real take.
[ "$mode" = prove ] && dir=''
project=''
sandbox=''
made_project=0
cleanup() {
  [ -n "$sandbox$project" ] || return 0
  if [ "$keep" -eq 1 ]; then
    printf 'agent-take: kept studio %s and sandbox %s\n' "$project" "$sandbox" >&2
    return 0
  fi
  [ -n "$sandbox" ] && rm -rf "$sandbox"
  if [ -n "$project" ]; then
    if [ "$made_project" -eq 1 ]; then rm -rf "$project"
    else find "$project" -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null
    fi
  fi
}
# Claude Code ignores a project settings file's allow rules until the folder
# is trusted, and records trust in the login dir's .claude.json as
# projects[PATH].hasTrustDialogAccepted (2.1.306 names the key when it
# refuses). Trust the studio there, in the dedicated login dir only.
pretrust_studio() {
  local file="$agent_config/.claude.json" script
  script='import json, os, sys
path, project = sys.argv[1], sys.argv[2]
data = json.load(open(path)) if os.path.exists(path) else {}
data.setdefault("projects", {}).setdefault(project, {})["hasTrustDialogAccepted"] = True
tmp = path + ".demo-reel-tmp"
with open(tmp, "w") as out:
    json.dump(data, out, indent=2)
os.replace(tmp, path)'
  if command -v python3 >/dev/null 2>&1; then
    python3 -c "$script" "$file" "$project" && return 0
  fi
  printf 'agent-take: could not pre-trust the studio (needs python3); answer the trust prompt in a rehearsal take\n' >&2
  return 0
}
if [ "$mode" = dry-run ]; then
  project=${dir:-'<new temp dir>'}
  sandbox='<new temp dir>'
else
  trap cleanup EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  if [ -n "$dir" ]; then
    if [ -e "$dir" ]; then
      [ -d "$dir" ] || die 4 "--dir exists and is not a directory: $dir"
      [ -z "$(ls -A "$dir" 2>/dev/null)" ] || die 4 "--dir must be new or empty: $dir"
    else
      mkdir -p "$dir" || die 4 "cannot create $dir"
      made_project=1
    fi
    project=$(cd "$dir" && pwd -P)
  else
    project=$(mktemp -d "${TMPDIR:-/tmp}/studio.XXXXXX") || die 4 'cannot create a studio dir'
    project=$(cd "$project" && pwd -P)
    made_project=1
  fi
  sandbox=$(mktemp -d "${TMPDIR:-/tmp}/studio-sandbox.XXXXXX") || die 4 'cannot create a sandbox dir'
  sandbox=$(cd "$sandbox" && pwd -P)
  mkdir -p "$sandbox/bin" "$sandbox/home" "$sandbox/xdg/config" "$sandbox/xdg/cache" \
    "$sandbox/xdg/data" "$sandbox/xdg/state" "$sandbox/zdotdir" "$sandbox/tmp" || die 4 'cannot build the sandbox'
  : >"$sandbox/zdotdir/.zshenv"
  : >"$sandbox/zdotdir/.zshrc"
  i=0
  while [ $i -lt ${#allow_paths[@]} ]; do
    ln -s "${allow_paths[$i]}" "$sandbox/bin/${allow_names[$i]}" || die 4 "cannot link ${allow_paths[$i]}"
    i=$((i + 1))
  done
  if [ "$agent" = claude ]; then skill_root="$project/.claude/skills"; else skill_root="$project/.agents/skills"; fi
  for skill in ${skills[@]+"${skills[@]}"}; do
    # -L copies link targets, which the check above kept inside the skill.
    mkdir -p "$skill_root" && cp -RL "$skill" "$skill_root/$(basename "$skill")" || die 4 "cannot copy skill $skill"
  done
  printf '%s\n' "$prompt" >"$sandbox/studio-prompt.txt"
  if [ "$agent" = claude ]; then
    mkdir -p "$project/.claude" || die 4 'cannot write the studio settings'
    settings_json >"$project/.claude/settings.json"
    cp "$project/.claude/settings.json" "$sandbox/settings.json"
    if [ "$real_home" -eq 0 ] && [ -d "$agent_config" ]; then pretrust_studio; fi
  else
    # Codex reads project instructions from AGENTS.md in its working root.
    printf '%s\n' "$prompt" >"$project/AGENTS.md"
  fi
fi

shell=/bin/bash
[ -x /bin/zsh ] && shell=/bin/zsh
if [ "$real_home" -eq 1 ]; then take_home=$HOME; else take_home="$sandbox/home"; fi

base_env=(
  "HOME=$take_home"
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
if [ "$real_home" -eq 0 ]; then
  base_env+=("$config_var=$agent_config")
else
  eval "value=\${$config_var-}"
  [ -n "$value" ] && base_env+=("$config_var=$value")
fi
if [ "$agent" = claude ]; then
  base_env+=(CLAUDE_CODE_DISABLE_CLAUDE_MDS=1 CLAUDE_CODE_DISABLE_AUTO_MEMORY=1)
  auth_names='ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL'
else
  auth_names='OPENAI_API_KEY OPENAI_BASE_URL'
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

argv=("${launch[@]}")
if [ "$agent" = claude ]; then
  tool_names=''
  for rule in "${rules[@]}"; do
    tool=${rule%%(*}
    case ",$tool_names," in *",$tool,"*) ;; *) tool_names="${tool_names:+$tool_names,}$tool" ;; esac
  done
  argv+=(--settings "$sandbox/settings.json" --setting-sources project,local --strict-mcp-config
    --permission-mode dontAsk --tools "$tool_names" --allowedTools "${rules[@]}"
    --append-system-prompt "$prompt")
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

notes=(
  "This is a set of brakes, not isolation: env -i does not stop a command from running any system binary by absolute path."
  "The OS keychain or secret service is reached by user identity, not HOME; a product that keeps credentials there can still find them."
)
if [ "$real_home" -eq 1 ]; then
  notes+=("--real-home: the take runs with the real HOME, so dotfiles and config under it are reachable by any allowed binary.")
fi
if [ "$agent" = claude ]; then
  notes+=("blockReadsOutsideWorkingDirectories covers the file tools (Read, Grep, Glob, LSP) and the Bash commands Claude Code recognizes as file reads; a command an allow rule approves, such as jq on a path under Bash(jq *), may still read outside the studio.")
else
  notes+=("Codex has no per-command allowlist here. In testing its sandbox blocked network access and writes outside the workspace, but read files under HOME.")
fi

# Codex's sandbox needs platform support (bubblewrap with user namespaces on
# Linux). Find out before the take rather than mid-take, and never fall back.
# The preflight runs in the studio; codex sandbox -C also demands a
# --permission-profile in 0.163.0, so it is not passed.
codex_preflight() {
  local out status truth=/usr/bin/true
  [ -x "$truth" ] || truth=/bin/true
  # The preflight needs no login, so it gets a scratch CODEX_HOME.
  mkdir -p "$sandbox/codex-preflight"
  out=$( (cd "$project" && env -i "${take_env[@]}" "CODEX_HOME=$sandbox/codex-preflight" \
    "${launch[@]}" sandbox -- "$truth") 2>&1)
  status=$?
  if [ $status -ne 0 ]; then
    preflight_detail=$(printf '%s' "$out" | head -n 3 | tr '\n' ' ' | cut -c1-300)
    return 1
  fi
  preflight_detail="codex sandbox ran $truth"
  return 0
}

if [ "$mode" = dry-run ]; then
  shown=()
  for pair in "${take_env[@]}"; do shown+=("$(masked "$pair")"); done
  if [ "$json" -eq 1 ]; then
    printf '{"agent": %s, "bin": %s, "interpreter": %s, "project": %s, "sandbox": %s,\n' \
      "$(json_str "$agent")" "$(json_str "$agent_bin")" "$(json_str "$interpreter")" "$(json_str "$project")" "$(json_str "$sandbox")"
    printf ' "agent_config": %s, "real_home": %s,\n' "$(json_str "$agent_config")" \
      "$([ "$real_home" -eq 1 ] && printf true || printf false)"
    printf ' "env": %s,\n' "$(json_array "${shown[@]}")"
    printf ' "argv": %s,\n' "$(json_array "${argv[@]}")"
    if [ "$agent" = claude ]; then printf ' "settings": %s,\n' "$(json_str "$(settings_json)")"; fi
    printf ' "skills": %s, "allowed": %s, "notes": %s}\n' \
      "$(json_array ${skills[@]+"${skills[@]}"})" "$(json_array ${allow_paths[@]+"${allow_paths[@]}"})" "$(json_array "${notes[@]}")"
  else
    printf 'studio   %s  (the agent'"'"'s working directory)\n' "$project"
    printf 'sandbox  %s\n' "$sandbox"
    printf 'login    %s=%s\n' "$config_var" "$agent_config"
    [ -n "$interpreter" ] && printf 'script   %s runs through %s\n' "$agent_bin" "$interpreter"
    for skill in ${skills[@]+"${skills[@]}"}; do printf 'skill    %s\n' "$skill"; done
    i=0
    while [ $i -lt ${#allow_paths[@]} ]; do printf 'allow    %s -> %s\n' "${allow_names[$i]}" "${allow_paths[$i]}"; i=$((i + 1)); done
    printf '\ncd %q &&\nenv -i \\\n' "$project"
    for pair in "${shown[@]}"; do printf '  %q \\\n' "$pair"; done
    last=$((${#argv[@]} - 1))
    i=0
    for word in "${argv[@]}"; do
      if [ $i -lt $last ]; then printf '  %q \\\n' "$word"; else printf '  %q\n' "$word"; fi
      i=$((i + 1))
    done
    if [ "$agent" = claude ]; then printf '\n.claude/settings.json (also passed with --settings):\n'; settings_json; fi
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
  # watched_files -> files present in the XDG dirs and the throwaway HOME
  watched_files() {
    local d
    for d in "$sandbox/xdg/config" "$sandbox/xdg/cache" "$sandbox/xdg/data" "$sandbox/xdg/state"; do
      (cd "$d" && find . -mindepth 1 | sed "s|^\\.|${d#"$sandbox"/}|")
    done
    [ "$real_home" -eq 1 ] || (cd "$sandbox/home" && find . -mindepth 1 | sed 's|^\.|home|')
  }

  if [ -n "$interpreter" ]; then
    record launch ok "$agent_bin runs through $interpreter by absolute path"
  else
    record launch ok "$agent_bin is a native binary"
  fi
  if [ "$agent" = codex ]; then
    if codex_preflight; then record codex ok "$preflight_detail"
    else record codex fail "Codex's sandbox cannot start here: $preflight_detail"; fi
  fi

  listed=$(ls -A "$sandbox/bin" | sort | tr '\n' ' ')
  wanted=$(printf '%s\n' ${allow_names[@]+"${allow_names[@]}"} | sed '/^$/d' | sort | tr '\n' ' ')
  if [ "$listed" = "$wanted" ]; then record path ok "PATH holds only: ${listed:-nothing}"
  else record path fail "PATH holds $listed; expected $wanted"; fi

  stranded=''
  i=0
  while [ $i -lt ${#allow_paths[@]} ]; do
    if line=$(shebang_of "${allow_paths[$i]}"); then
      set -f
      set -- $line
      set +f
      if [ "$(basename "$1")" = env ]; then
        shift
        [ "${1:-}" = -S ] && shift
        case " ${allow_names[*]} " in *" ${1:-} "*) ;; *) stranded="$stranded ${allow_names[$i]}(needs ${1:-?})" ;; esac
      fi
    fi
    i=$((i + 1))
  done
  if [ -z "$stranded" ]; then record scripts ok 'every allowed script can find its interpreter'
  else record scripts fail "allowed scripts whose interpreter is not allowed:$stranded"; fi

  escaped=''
  for tool in curl wget ssh scp nc cat env python3 python node perl ruby git sh bash zsh sudo open xdg-open security; do
    case " ${allow_names[*]-} " in *" $tool "*) continue ;; esac
    if in_sandbox take_env "command -v $tool" >/dev/null; then escaped="$escaped $tool"; fi
  done
  if [ -z "$escaped" ]; then record tools ok 'no common shell, network or file tool is on PATH (absolute paths still run; the allowlist is the guard)'
  else record tools fail "on PATH without being allowed:$escaped"; fi

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

  links=$(find "$project" -type l 2>/dev/null | sed "s|^$project/||" | tr '\n' ' ')
  if [ -z "$links" ]; then record links ok 'the studio holds no symlinks'
  else record links fail "symlinks in the studio: $links"; fi

  before=$(watched_files)
  if [ -z "$before" ]; then record empty ok 'XDG dirs and the throwaway HOME start empty'
  else record empty fail "not empty before the probes: $(printf '%s' "$before" | tr '\n' ' ')"; fi

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

  # A probe that writes config (a product migrating a legacy file, say) is a
  # leak too. Names only: never print what was written.
  after=$(watched_files)
  if [ "$after" = "$before" ]; then record writes ok 'the probes wrote nothing to the XDG dirs or HOME'
  else record writes fail "written during the probes (names only): $(printf '%s' "$after" | tr '\n' ' ')"; fi

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
    printf '], "cleaned_up": %s, "notes": %s}\n' "$([ "$keep" -eq 1 ] && printf false || printf true)" \
      "$(json_array "${notes[@]}")"
  else
    printf '%s' "$results" | awk -F'\t' 'NF >= 2 { printf "%-4s %-7s %s\n", ($2 == "ok" ? "ok" : "FAIL"), $1, $3 }'
    printf '%s' "$probe_rows" | awk -F'\t' 'NF >= 3 {
      mark = ($3 == "ok") ? "ok" : (($3 == "fail") ? "FAIL" : "look")
      printf "%-4s probe   %s (exit %s)\n        %s\n", mark, $1, $2, $4 }'
    for note in "${notes[@]}"; do printf 'note: %s\n' "$note"; done
    if [ "$failed" -eq 0 ]; then printf 'sandbox holds\n'; else printf 'sandbox leaks\n'; fi
  fi
  exit "$failed"
fi

if [ "$agent" = codex ] && ! codex_preflight; then
  die 3 "Codex's sandbox cannot start here ($preflight_detail). On Linux this usually means bubblewrap cannot create user namespaces; enable them or film on another host. There is no fallback to full access."
fi
if [ "$real_home" -eq 1 ]; then
  printf 'agent-take: WARNING: --real-home: this take can reach everything under %s\n' "$HOME" >&2
fi

# Launch. Run the agent as a child, never with exec: an exec'd take that
# exits closes the terminal window the camera is filming. Ctrl-C belongs to
# the agent while it runs; a no-op trap (unlike an ignored signal) is not
# inherited, so the agent still receives it and the launcher keeps going.
trap ':' INT
(cd "$project" && env -i "${take_env[@]}" "${argv[@]}")
status=$?
trap 'exit 130' INT
{
  printf '\nagent-take: take ended (exit %s)\n' "$status"
  if [ "$real_home" -eq 1 ]; then
    printf '  Transcripts stay in the agent'"'"'s normal config dir; read them before sharing.\n'
  elif [ "$agent" = claude ]; then
    printf '  Transcripts stay under %s/projects/; read them before sharing.\n' "$agent_config"
  else
    printf '  Session logs stay under %s/sessions/; read them before sharing.\n' "$agent_config"
  fi
  [ "$keep" -eq 1 ] || printf '  The studio and sandbox are deleted on exit (--keep to inspect them).\n'
} >&2
exit "$status"
