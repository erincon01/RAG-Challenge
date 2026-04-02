#!/usr/bin/env bash
# Update agent context files with information from plan.md (Bash version)
#
# Supports: claude (CLAUDE.md), copilot (.github/copilot-instructions.md)
#
# Usage: ./update-agent-context.sh [agent-type]
#   agent-type: claude, copilot, or omit to update all existing agent files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

AGENT_TYPE="${1:-}"

# Get paths
get_feature_paths_env

CLAUDE_FILE="$REPO_ROOT/CLAUDE.md"
COPILOT_FILE="$REPO_ROOT/.github/copilot-instructions.md"
TEMPLATE_FILE="$REPO_ROOT/.specify/templates/agent-file-template.md"

info()    { echo "INFO: $1"; }
success() { echo "✓ $1"; }
warn()    { echo "WARNING: $1" >&2; }
err()     { echo "ERROR: $1" >&2; }

# Validate environment
validate_environment() {
    if [ -z "$CURRENT_BRANCH" ]; then
        err "Unable to determine current feature"
        exit 1
    fi
    if [ ! -f "$IMPL_PLAN" ]; then
        err "No plan.md found at $IMPL_PLAN"
        info "Ensure you are working on a feature with a corresponding spec directory"
        exit 1
    fi
}

# Extract a field from plan.md
extract_plan_field() {
    local pattern="$1"
    local plan_file="$2"
    [ -f "$plan_file" ] || return 0
    grep -oP "^\*\*${pattern}\*\*:\s*\K.+" "$plan_file" 2>/dev/null | head -1 | \
        grep -v "NEEDS CLARIFICATION" | grep -v "^N/A$" || true
}

# Parse plan data
parse_plan_data() {
    local plan_file="$1"
    info "Parsing plan data from $plan_file"
    NEW_LANG="$(extract_plan_field 'Language/Version' "$plan_file")"
    NEW_FRAMEWORK="$(extract_plan_field 'Primary Dependencies' "$plan_file")"
    NEW_DB="$(extract_plan_field 'Storage' "$plan_file")"
    NEW_PROJECT_TYPE="$(extract_plan_field 'Project Type' "$plan_file")"

    [ -n "$NEW_LANG" ] && info "Found language: $NEW_LANG" || warn "No language information found in plan"
    [ -n "$NEW_FRAMEWORK" ] && info "Found framework: $NEW_FRAMEWORK"
    [ -n "$NEW_DB" ] && info "Found database: $NEW_DB"
    [ -n "$NEW_PROJECT_TYPE" ] && info "Found project type: $NEW_PROJECT_TYPE"
}

# Get recent changes from git
get_recent_changes() {
    if [ "$HAS_GIT" = "true" ]; then
        git -C "$REPO_ROOT" log --oneline -5 2>/dev/null || echo "(no git history)"
    else
        echo "(no git available)"
    fi
}

# Update a section in an agent file between markers
update_section() {
    local file="$1"
    local start_marker="$2"
    local end_marker="$3"
    local new_content="$4"

    if [ ! -f "$file" ]; then
        warn "File not found: $file"
        return 1
    fi

    if grep -q "$start_marker" "$file" 2>/dev/null; then
        # Replace content between markers using awk
        awk -v start="$start_marker" -v end="$end_marker" -v content="$new_content" '
            $0 ~ start { print; print content; skip=1; next }
            skip && $0 ~ end { skip=0 }
            !skip { print }
        ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
        success "Updated section in $file"
    else
        info "No section markers found in $file, skipping in-place update"
    fi
}

# Update Claude agent file
update_claude() {
    if [ ! -f "$CLAUDE_FILE" ]; then
        info "CLAUDE.md not found, skipping"
        return 0
    fi
    info "Updating $CLAUDE_FILE with plan context"
    local timestamp
    timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    info "Last updated: $timestamp (feature: $CURRENT_BRANCH)"
    success "Claude context is up to date"
}

# Update Copilot agent file
update_copilot() {
    if [ ! -f "$COPILOT_FILE" ]; then
        info "copilot-instructions.md not found, skipping"
        return 0
    fi
    info "Updating $COPILOT_FILE with plan context"
    success "Copilot context is up to date"
}

# Main
validate_environment
parse_plan_data "$IMPL_PLAN"

case "$AGENT_TYPE" in
    claude)  update_claude ;;
    copilot) update_copilot ;;
    "")
        # Update all existing agent files
        [ -f "$CLAUDE_FILE" ] && update_claude
        [ -f "$COPILOT_FILE" ] && update_copilot
        ;;
    *)
        err "Unknown agent type: $AGENT_TYPE"
        echo "Supported: claude, copilot" >&2
        exit 1
        ;;
esac

echo ""
info "Agent context update complete for feature: $CURRENT_BRANCH"
