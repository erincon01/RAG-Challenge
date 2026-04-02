#!/usr/bin/env bash
# Common bash functions analogous to common.ps1

set -euo pipefail

# Find repository root by searching upward for .specify directory
find_specify_root() {
    local current
    current="$(cd "${1:-.}" && pwd)"

    while true; do
        if [ -d "$current/.specify" ]; then
            echo "$current"
            return 0
        fi
        local parent
        parent="$(dirname "$current")"
        if [ "$parent" = "$current" ]; then
            return 1
        fi
        current="$parent"
    done
}

# Get repository root, prioritizing .specify directory over git
get_repo_root() {
    local specify_root
    if specify_root="$(find_specify_root)"; then
        echo "$specify_root"
        return 0
    fi

    # Fallback to git
    if command -v git &>/dev/null; then
        local git_root
        if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
            echo "$git_root"
            return 0
        fi
    fi

    # Final fallback to script location
    echo "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
}

# Get current branch name
get_current_branch() {
    # First check SPECIFY_FEATURE environment variable
    if [ -n "${SPECIFY_FEATURE:-}" ]; then
        echo "$SPECIFY_FEATURE"
        return 0
    fi

    # Then check git
    local repo_root
    repo_root="$(get_repo_root)"
    if test_has_git; then
        local branch
        if branch="$(git -C "$repo_root" rev-parse --abbrev-ref HEAD 2>/dev/null)"; then
            echo "$branch"
            return 0
        fi
    fi

    # For non-git repos, find latest feature directory
    local specs_dir="$repo_root/specs"
    if [ -d "$specs_dir" ]; then
        local latest=""
        local highest=0
        local latest_ts=""

        for dir in "$specs_dir"/*/; do
            [ -d "$dir" ] || continue
            local name
            name="$(basename "$dir")"

            if [[ "$name" =~ ^([0-9]{8}-[0-9]{6})- ]]; then
                local ts="${BASH_REMATCH[1]}"
                if [[ "$ts" > "$latest_ts" ]]; then
                    latest_ts="$ts"
                    latest="$name"
                fi
            elif [[ "$name" =~ ^([0-9]{3,})- ]]; then
                local num="${BASH_REMATCH[1]}"
                num=$((10#$num))
                if [ "$num" -gt "$highest" ]; then
                    highest=$num
                    if [ -z "$latest_ts" ]; then
                        latest="$name"
                    fi
                fi
            fi
        done

        if [ -n "$latest" ]; then
            echo "$latest"
            return 0
        fi
    fi

    echo "main"
}

# Check if git is available at the spec-kit root level
test_has_git() {
    command -v git &>/dev/null || return 1
    local repo_root
    repo_root="$(get_repo_root)"
    [ -e "$repo_root/.git" ] || return 1
    git -C "$repo_root" rev-parse --is-inside-work-tree &>/dev/null
}

# Validate feature branch naming
test_feature_branch() {
    local branch="$1"
    local has_git="${2:-true}"

    if [ "$has_git" != "true" ]; then
        echo "WARNING: Git repository not detected; skipped branch validation" >&2
        return 0
    fi

    if [[ ! "$branch" =~ ^[0-9]{3,}- ]] && [[ ! "$branch" =~ ^[0-9]{8}-[0-9]{6}- ]]; then
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        echo "Feature branches should be named like: 001-feature-name or 20260319-143022-feature-name" >&2
        return 1
    fi
    return 0
}

# Get feature directory path
get_feature_dir() {
    local repo_root="$1"
    local branch="$2"
    echo "$repo_root/specs/$branch"
}

# Export all feature path variables
get_feature_paths_env() {
    local repo_root
    repo_root="$(get_repo_root)"
    local current_branch
    current_branch="$(get_current_branch)"
    local has_git="false"
    if test_has_git; then has_git="true"; fi
    local feature_dir
    feature_dir="$(get_feature_dir "$repo_root" "$current_branch")"

    REPO_ROOT="$repo_root"
    CURRENT_BRANCH="$current_branch"
    HAS_GIT="$has_git"
    FEATURE_DIR="$feature_dir"
    FEATURE_SPEC="$feature_dir/spec.md"
    IMPL_PLAN="$feature_dir/plan.md"
    TASKS="$feature_dir/tasks.md"
    RESEARCH="$feature_dir/research.md"
    DATA_MODEL="$feature_dir/data-model.md"
    QUICKSTART="$feature_dir/quickstart.md"
    CONTRACTS_DIR="$feature_dir/contracts"
}

# Test if a file exists and print status
test_file_exists() {
    local path="$1"
    local description="$2"
    if [ -f "$path" ]; then
        echo "  ✓ $description"
        return 0
    else
        echo "  ✗ $description"
        return 1
    fi
}

# Test if a directory has files
test_dir_has_files() {
    local path="$1"
    local description="$2"
    if [ -d "$path" ] && [ -n "$(ls -A "$path" 2>/dev/null)" ]; then
        echo "  ✓ $description"
        return 0
    else
        echo "  ✗ $description"
        return 1
    fi
}

# Resolve template using priority stack
resolve_template() {
    local template_name="$1"
    local repo_root="$2"
    local base="$repo_root/.specify/templates"

    # Priority 1: Project overrides
    local override="$base/overrides/$template_name.md"
    if [ -f "$override" ]; then echo "$override"; return 0; fi

    # Priority 2: Installed presets (alphabetical fallback)
    local presets_dir="$repo_root/.specify/presets"
    if [ -d "$presets_dir" ]; then
        for preset in "$presets_dir"/*/; do
            [ -d "$preset" ] || continue
            local pname
            pname="$(basename "$preset")"
            [[ "$pname" == .* ]] && continue
            local candidate="$preset/templates/$template_name.md"
            if [ -f "$candidate" ]; then echo "$candidate"; return 0; fi
        done
    fi

    # Priority 3: Extension-provided templates
    local ext_dir="$repo_root/.specify/extensions"
    if [ -d "$ext_dir" ]; then
        for ext in "$ext_dir"/*/; do
            [ -d "$ext" ] || continue
            local ename
            ename="$(basename "$ext")"
            [[ "$ename" == .* ]] && continue
            local candidate="$ext/templates/$template_name.md"
            if [ -f "$candidate" ]; then echo "$candidate"; return 0; fi
        done
    fi

    # Priority 4: Core templates
    local core="$base/$template_name.md"
    if [ -f "$core" ]; then echo "$core"; return 0; fi

    return 1
}
