#!/usr/bin/env bash
# Create a new feature
#
# Usage: ./create-new-feature.sh [OPTIONS] <feature description>
#
# OPTIONS:
#   --json                 Output in JSON format
#   --allow-existing       Switch to branch if it already exists
#   --short-name <name>    Provide a custom short name (2-4 words) for the branch
#   --number <N>           Specify branch number manually
#   --timestamp            Use timestamp prefix instead of sequential numbering
#   --help, -h             Show help message

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

# Parse arguments
JSON=false
ALLOW_EXISTING=false
SHORT_NAME=""
NUMBER=0
TIMESTAMP=false
FEATURE_DESC=""

while [ $# -gt 0 ]; do
    case "$1" in
        --json)             JSON=true ;;
        --allow-existing)   ALLOW_EXISTING=true ;;
        --short-name)       shift; SHORT_NAME="$1" ;;
        --number)           shift; NUMBER="$1" ;;
        --timestamp)        TIMESTAMP=true ;;
        --help|-h)
            cat <<'HELP'
Usage: ./create-new-feature.sh [OPTIONS] <feature description>

OPTIONS:
  --json                 Output in JSON format
  --allow-existing       Switch to branch if it already exists
  --short-name <name>    Provide a custom short name for the branch
  --number <N>           Specify branch number manually
  --timestamp            Use timestamp prefix instead of sequential numbering
  --help, -h             Show this help message

EXAMPLES:
  ./create-new-feature.sh 'Add user authentication system' --short-name 'user-auth'
  ./create-new-feature.sh 'Implement OAuth2 integration for API'
  ./create-new-feature.sh --timestamp --short-name 'user-auth' 'Add user authentication'
HELP
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2; exit 1 ;;
        *)
            if [ -z "$FEATURE_DESC" ]; then
                FEATURE_DESC="$1"
            else
                FEATURE_DESC="$FEATURE_DESC $1"
            fi
            ;;
    esac
    shift
done

FEATURE_DESC="$(echo "$FEATURE_DESC" | xargs)"

if [ -z "$FEATURE_DESC" ]; then
    echo "Error: Feature description is required" >&2
    echo "Usage: ./create-new-feature.sh [OPTIONS] <feature description>" >&2
    exit 1
fi

# Helper: clean branch name
clean_branch_name() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g; s/-\{2,\}/-/g; s/^-//; s/-$//'
}

# Helper: get highest number from specs directories
get_highest_from_specs() {
    local specs_dir="$1"
    local highest=0
    if [ -d "$specs_dir" ]; then
        for dir in "$specs_dir"/*/; do
            [ -d "$dir" ] || continue
            local name
            name="$(basename "$dir")"
            if [[ "$name" =~ ^([0-9]{3,})- ]] && [[ ! "$name" =~ ^[0-9]{8}-[0-9]{6}- ]]; then
                local num=$((10#${BASH_REMATCH[1]}))
                if [ "$num" -gt "$highest" ]; then highest=$num; fi
            fi
        done
    fi
    echo "$highest"
}

# Helper: get highest number from git branches
get_highest_from_branches() {
    local highest=0
    if command -v git &>/dev/null; then
        while IFS= read -r branch; do
            branch="$(echo "$branch" | sed 's/^[* ]*//' | sed 's|^remotes/[^/]*/||')"
            if [[ "$branch" =~ ^([0-9]{3,})- ]] && [[ ! "$branch" =~ ^[0-9]{8}-[0-9]{6}- ]]; then
                local num=$((10#${BASH_REMATCH[1]}))
                if [ "$num" -gt "$highest" ]; then highest=$num; fi
            fi
        done < <(git branch -a 2>/dev/null || true)
    fi
    echo "$highest"
}

# Helper: generate branch name from description with stop word filtering
get_branch_name() {
    local desc="$1"
    local stop_words="i a an the to for of in on at by with from is are was were be been being have has had do does did will would should could can may might must shall this that these those my your our their want need add get set"

    local clean
    clean="$(echo "$desc" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9 ]/ /g')"
    local words=()

    for word in $clean; do
        local is_stop=false
        for sw in $stop_words; do
            if [ "$word" = "$sw" ]; then is_stop=true; break; fi
        done
        if [ "$is_stop" = false ] && [ "${#word}" -ge 3 ]; then
            words+=("$word")
        fi
    done

    if [ "${#words[@]}" -gt 0 ]; then
        local max=3
        if [ "${#words[@]}" -eq 4 ]; then max=4; fi
        local result=""
        local count=0
        for w in "${words[@]}"; do
            if [ "$count" -ge "$max" ]; then break; fi
            if [ -n "$result" ]; then result="$result-"; fi
            result="$result$w"
            count=$((count + 1))
        done
        echo "$result"
    else
        clean_branch_name "$desc" | cut -d'-' -f1-3
    fi
}

# Main logic
REPO_ROOT="$(get_repo_root)"
HAS_GIT=false
if test_has_git; then HAS_GIT=true; fi

cd "$REPO_ROOT"

SPECS_DIR="$REPO_ROOT/specs"
mkdir -p "$SPECS_DIR"

# Generate branch suffix
if [ -n "$SHORT_NAME" ]; then
    BRANCH_SUFFIX="$(clean_branch_name "$SHORT_NAME")"
else
    BRANCH_SUFFIX="$(get_branch_name "$FEATURE_DESC")"
fi

# Warn if both --number and --timestamp
if [ "$TIMESTAMP" = true ] && [ "$NUMBER" -ne 0 ]; then
    echo "WARNING: --number is ignored when --timestamp is used" >&2
    NUMBER=0
fi

# Determine branch prefix
if [ "$TIMESTAMP" = true ]; then
    FEATURE_NUM="$(date +%Y%m%d-%H%M%S)"
    BRANCH_NAME="$FEATURE_NUM-$BRANCH_SUFFIX"
else
    if [ "$NUMBER" -eq 0 ]; then
        if [ "$HAS_GIT" = true ]; then
            git fetch --all --prune 2>/dev/null || true
            HIGHEST_BRANCH="$(get_highest_from_branches)"
            HIGHEST_SPEC="$(get_highest_from_specs "$SPECS_DIR")"
            MAX_NUM="$HIGHEST_BRANCH"
            if [ "$HIGHEST_SPEC" -gt "$MAX_NUM" ]; then MAX_NUM="$HIGHEST_SPEC"; fi
            NUMBER=$((MAX_NUM + 1))
        else
            NUMBER=$(( $(get_highest_from_specs "$SPECS_DIR") + 1 ))
        fi
    fi
    FEATURE_NUM="$(printf '%03d' "$NUMBER")"
    BRANCH_NAME="$FEATURE_NUM-$BRANCH_SUFFIX"
fi

# Truncate to GitHub's 244-byte limit
if [ "${#BRANCH_NAME}" -gt 244 ]; then
    PREFIX_LEN=$(( ${#FEATURE_NUM} + 1 ))
    MAX_SUFFIX=$(( 244 - PREFIX_LEN ))
    BRANCH_SUFFIX="${BRANCH_SUFFIX:0:$MAX_SUFFIX}"
    BRANCH_SUFFIX="${BRANCH_SUFFIX%-}"
    echo "WARNING: Branch name truncated to 244 bytes" >&2
    BRANCH_NAME="$FEATURE_NUM-$BRANCH_SUFFIX"
fi

# Create or switch to git branch
if [ "$HAS_GIT" = true ]; then
    if ! git checkout -q -b "$BRANCH_NAME" 2>/dev/null; then
        if git branch --list "$BRANCH_NAME" | grep -q .; then
            if [ "$ALLOW_EXISTING" = true ]; then
                git checkout -q "$BRANCH_NAME" 2>/dev/null || {
                    echo "Error: Branch '$BRANCH_NAME' exists but could not be checked out." >&2
                    exit 1
                }
            else
                echo "Error: Branch '$BRANCH_NAME' already exists." >&2
                exit 1
            fi
        else
            echo "Error: Failed to create git branch '$BRANCH_NAME'." >&2
            exit 1
        fi
    fi
else
    echo "WARNING: Git repository not detected; skipped branch creation for $BRANCH_NAME" >&2
fi

# Create feature directory and spec file
FEATURE_DIR="$SPECS_DIR/$BRANCH_NAME"
mkdir -p "$FEATURE_DIR"

SPEC_FILE="$FEATURE_DIR/spec.md"
if [ ! -f "$SPEC_FILE" ]; then
    TEMPLATE="$(resolve_template 'spec-template' "$REPO_ROOT" 2>/dev/null || true)"
    if [ -n "$TEMPLATE" ] && [ -f "$TEMPLATE" ]; then
        cp "$TEMPLATE" "$SPEC_FILE"
    else
        touch "$SPEC_FILE"
    fi
fi

# Set environment variable
export SPECIFY_FEATURE="$BRANCH_NAME"

# Output
if [ "$JSON" = true ]; then
    printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_NUM":"%s","HAS_GIT":%s}\n' \
        "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_NUM" "$HAS_GIT"
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "FEATURE_NUM: $FEATURE_NUM"
    echo "HAS_GIT: $HAS_GIT"
    echo "SPECIFY_FEATURE environment variable set to: $BRANCH_NAME"
fi
