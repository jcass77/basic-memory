# Update Basic Memory AI Assistant Guide

## Overview

This SOP ensures the Basic Memory AI assistant guides align with user preferences by identifying and resolving contradictions. Regular alignment prevents drift from established standards and ensures predictable, preference-compliant AI behavior. It processes both the extended and abridged upstream guides.

## Parameters

- **preferences_path** (optional, default: "src/basic_memory/_personalization/config/user-preferences.md"): Path to user preferences file
- **output_dir** (optional, default: "src/basic_memory/_personalization/.scratchpad/update-basic-memory-ai-assistant-guide"): Directory for SOP output artifacts

**Guides to process:**

| Label | Upstream URL | Personalized Path |
|-------|-------------|-------------------|
| extended | https://raw.githubusercontent.com/basicmachines-co/basic-memory/refs/heads/main/docs/ai-assistant-guide-extended.md | docs/ai-assistant-guide-extended.md |
| abridged | https://raw.githubusercontent.com/basicmachines-co/basic-memory/refs/heads/main/src/basic_memory/mcp/resources/ai_assistant_guide.md | src/basic_memory/mcp/resources/ai_assistant_guide.md |

**Constraints for parameter acquisition:**
- If all required parameters are already provided, You MUST proceed to the Steps
- If any required parameters are missing, You MUST ask for them before proceeding
- When asking for parameters, You MUST request all parameters in a single prompt
- When asking for parameters, You MUST use the exact parameter names as defined
- You MUST validate that file paths exist before proceeding
- You MUST confirm successful acquisition of all parameters before proceeding

## Steps

### 1. Setup

Load current user preferences and download the latest upstream guides.

**Constraints:**
- You MUST read user preferences using `fs_read(path=preferences_path)`
- You MUST download both upstream guides using `web_fetch(url=<upstream_url>, mode="full")`
- You MUST NOT proceed if preferences cannot be loaded because alignment requires both documents

### 2. Detect Changes

#### 2.1 Load Personalized Guides

Load each personalized guide for comparison. If a personalized guide does not yet exist, create it by copying the upstream content as the starting point.

**Constraints:**
- You MUST read each personalized guide using `fs_read(path=<personalized_path>)`
- If a personalized guide does not exist, You MUST create it from the upstream content before proceeding

### 3. Analyze Contradictions

For each guide pair, compare the upstream and personalized versions against user preferences to identify disparities.

**Constraints:**
- You MUST process each guide pair independently
- You MUST check these key areas:
  - Forward References Policy
  - Edit Operation Methods (find_replace vs append)
  - Naming Conventions (kebab-case vs title case)
  - Category Conventions (singular vs plural)
  - Communication Style (direct vs verbose)
  - Instruction Format (positive vs negative guidance)
- You MUST classify contradictions using these categories:

**Complete Contradictions (require removal/replacement):**
- Forward references policy (guide encourages, preferences prohibit)
- Edit operation preferences (append vs find_replace)

Example:
- Guide: "Feel free to reference entities that don't exist yet - Basic Memory will resolve these when they're created later"
- Preferences: "Add entries in the 'Relations' section only when they point to existing notes because forward references create broken links"
- Resolution: Remove forward reference encouragement from guide

**Naming Convention Conflicts:**
- Entity naming in relations (Title Case vs kebab-case)

Example:
- Guide: `- relation_type [[Target Entity]]`
- Preferences: "Use kebab-case naming convention for all note names"
- Resolution: Update all relation examples to use lowercase kebab-case (e.g., [[target-entity]], [[api-specification]])

**Category Convention Conflicts:**
- Singular vs plural category names

Example:
- Guide: `- [fact] Objective information`
- Preferences: `- [facts]: Objective information`
- Resolution: Convert all singular category names to plural throughout guide

**Tool Usage Conflicts:**
- Edit operation method preferences

Example:
- Guide: `edit_note() with operation="append"`
- Preferences: "Use the find_replace operation to target specific sections"
- Resolution: Update guide to use `edit_note() with operation="find_replace"`

**Communication Style Conflicts:**
- Instruction format (negative vs positive)

Example:
- Guide: "Don't create forward references"
- Preferences: Direct, positive instruction format
- Resolution: Convert to "Create relations only to existing notes"

### 4. Document Findings

#### 4.1 Create Contradiction Analysis

Document all identified contradictions for each guide.

**Constraints:**
- You MUST create output directory if it doesn't exist using `execute_bash(command="mkdir -p {output_dir}")`
- You MUST create `{output_dir}/preference-contradictions.md` with detailed findings for all guides
- You MUST include specific examples from both documents for each contradiction

#### 4.2 Create Task List

Generate numbered task list for systematic resolution.

**Constraints:**
- You MUST create `{output_dir}/contradiction-resolution-tasks.md` with actionable items
- You MUST use markdown checkbox format for tracking
- You MUST group tasks by guide label (extended, abridged)

### 5. Execute Resolution

Systematically resolve each identified contradiction in each personalized guide.

**Constraints:**
- You MUST resolve complete contradictions by removing/replacing conflicting content
- You MUST update naming conventions to use lowercase kebab-case in all relation examples
- You MUST convert all singular category names to plural form
- You MUST convert negative instructions to positive format
- You MUST use `sed` for batch transformations where patterns are repetitive because this is more efficient than individual str_replace calls
- You MUST use `fs_write` with `str_replace` for targeted edits that sed cannot handle
- You MUST NOT modify the upstream guides because they serve as the reference source
- You MUST process each guide independently because they have different content and scope

### 6. Verify Resolution

Perform final validation to ensure all contradictions are resolved in each personalized guide.

**Constraints:**
- You MUST run the validation script against each personalized guide:
  ```bash
  python -m scripts.guide_validation <personalized_path>
  ```
- If the script reports violations, You MUST fix them before proceeding
- You MUST mark completed tasks in the task list
- You MUST report the final validation output to the user

## Desired Outcome

- Both personalized guides fully aligned with user preferences
- No forward reference encouragement in either guide
- All edit examples use find_replace operation
- All entity/relation examples use lowercase kebab-case
- All category names use plural form
- All tasks marked as completed

## Examples

### Example 1: Default Usage
**Input:**
- All parameters use defaults

**Expected Behavior:**
Agent downloads both upstream guides, compares each against `src/basic_memory/_personalization/config/user-preferences.md`, identifies contradictions, creates analysis artifacts in `src/basic_memory/_personalization/.scratchpad/update-basic-memory-ai-assistant-guide/`, and resolves all issues in both personalized guides.

### Example 2: Custom Paths
**Input:**
- preferences_path: "src/basic_memory/_personalization/config/custom-preferences.md"
- output_dir: "src/basic_memory/_personalization/.scratchpad/guide-update-may"

**Expected Behavior:**
Agent uses the custom preferences path. Contradiction analysis and task list are written to `src/basic_memory/_personalization/.scratchpad/guide-update-may/`. Resolution edits target both personalized guide paths.

## Troubleshooting

### Contradictions Persist After Resolution
If search still finds contradiction patterns:
1. Re-read user preferences for recent updates
2. Check for missed examples in guide sections
3. Verify search patterns catch all instances

### File Operations Fail
If fs_write operations fail:
1. Check file paths and permissions
2. Verify old_str matches exactly (including whitespace)
3. Retry individual operations as needed

### Personalized Guide Does Not Exist
If a personalized guide is missing:
1. The SOP will create it from the upstream content
2. All transformations will be applied to the fresh copy
3. This is the expected path for first-time setup

## Artifacts

- `{output_dir}/preference-contradictions.md` - Detailed contradiction analysis
- `{output_dir}/contradiction-resolution-tasks.md` - Task checklist for resolution
- `docs/ai-assistant-guide-extended.md` - Updated extended personalized guide
- `src/basic_memory/mcp/resources/ai_assistant_guide.md` - Updated abridged personalized guide
