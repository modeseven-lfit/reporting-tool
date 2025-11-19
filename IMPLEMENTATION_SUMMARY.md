<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Implementation Summary: GitHub Pages URL Structure Changes

**Date:** 2025-01-19
**Author:** Claude (AI Assistant)
**Status:** Ready for Implementation
**Review Required:** Yes - Do not commit without review

---

## Overview

This document summarizes all changes required to fix GitHub Pages URL structure and resolve current issues.

### Key Changes

1. **URL Schema Change:** `pr-preview` → `previews`
2. **Production Location:** `/production/` → `/` (root level)
3. **Parent Index:** Add missing parent index for previews
4. **API Statistics:** Fix empty statistics table in workflow summary

---

## Current Issues

### ❌ Issue 1: All Report URLs Return 404

- Production URLs fail: `/reporting-tool/production/`
- Preview URLs fail: `/reporting-tool/pr-preview/`
- Root cause: Path generation issues in scripts

### ❌ Issue 2: Missing Preview Parent Index

- No index page at `/previews/` to list all PR previews
- Users cannot discover what previews exist
- Direct links work but no navigation

### ⚠️ Issue 3: Empty API Statistics Table

- Workflow shows "📊 API Statistics" heading
- Table content missing underneath
- Root cause: Code returns before completion when no API calls made

---

## Proposed URL Structure

### Before (Current)

```text
/reporting-tool/
├── index.html                     # Landing page with links
├── production/
│   ├── index.html                 # Production reports list
│   ├── onap/report.html
│   └── o-ran-sc/report.html
└── pr-preview/
    └── 6/
        ├── index.html
        ├── onap/report.html
        └── o-ran-sc/report.html
```

### After (Target)

```text
/reporting-tool/
├── index.html                     # Production reports list (ROOT)
├── onap/report.html              # Production reports at root
├── o-ran-sc/report.html
├── agl/report.html
└── previews/
    ├── index.html                 # NEW: Lists all PR previews
    └── 6/
        ├── index.html             # PR #6 preview reports list
        ├── onap/report.html
        └── o-ran-sc/report.html
```

### URL Examples

| Type | Before | After |
|------|--------|-------|
| Production Index | `/reporting-tool/production/` | `/reporting-tool/` |
| Production Report | `/reporting-tool/production/onap/report.html` | `/reporting-tool/onap/report.html` |
| Preview Parent | ❌ Missing | `/reporting-tool/previews/` |
| Preview Index | `/reporting-tool/pr-preview/6/` | `/reporting-tool/previews/6/` |
| Preview Report | `/reporting-tool/pr-preview/6/onap/report.html` | `/reporting-tool/previews/6/onap/report.html` |

---

## Implementation Details

### Phase 1: Update Preview Workflow (Low Risk)

**File:** `.github/workflows/reporting-previews.yaml`

**Status:** ✅ Already updated (pr-preview → previews)

**Changes Made:**

- Changed directory from `pr-preview/$pr_number` to `previews/$pr_number`
- Updated artifact names: `pr-preview-*` → `previews-*`
- Updated environment metadata: `"pr-preview"` → `"previews"`
- Updated all path references in bash scripts

**Remaining Work:**

- Add step to generate parent previews index (see PRODUCTION_AT_ROOT_CHANGES.md)
- Update git add to include `previews/index.html`

---

### Phase 2: Move Production to Root (Medium Risk)

**Files:**

- `.github/workflows/reporting-production.yaml`
- `.github/scripts/generate-index.sh`

**Changes Required:**

#### A. Update Production Workflow

Change reports directory from `production/$slug` to `$slug` (root level):

```yaml
# OLD:
target_dir="production/$slug"

# NEW:
target_dir="$slug"
```

Change generate-index.sh invocation:

```yaml
# OLD:
bash /tmp/main-scripts/generate-index.sh production

# NEW:
bash /tmp/main-scripts/generate-index.sh . production
```

Change git add commands:

```yaml
# OLD:
git add production/

# NEW:
for project_dir in */; do
  if [ -d "$project_dir" ] && [ "$project_dir" != "previews/" ] && [ -f "$project_dir/report.html" ]; then
    git add "$project_dir"
  fi
done
```

#### B. Update generate-index.sh Script

**Key Changes:**

1. Handle `REPORT_DIR="."` for root-level reports
2. Update BASE_PATH logic:
   - Production: `BASE_PATH="/${REPO_NAME}"`
   - Previews: `BASE_PATH="/${REPO_NAME}/${REPORT_DIR}"`
3. Exclude `previews/` directory when finding reports at root
4. Write index to `index.html` (not `./index.html` or `production/index.html`)

**Example:**

```bash
if [ "$ENVIRONMENT" = "previews" ]; then
  BASE_PATH="/${REPO_NAME}/${REPORT_DIR}"
else
  BASE_PATH="/${REPO_NAME}"
fi
```

---

### Phase 3: Add Parent Preview Index (Low Risk)

**File:** `.github/workflows/reporting-previews.yaml`

**New Step:** Add after "Generate preview index page"

**Purpose:**

- Generate `/previews/index.html` that lists all PR previews
- Shows PR number, project count, link to preview
- Sorts by PR number (descending, newest first)
- Shows empty state if no previews exist

**Implementation:**
See PRODUCTION_AT_ROOT_CHANGES.md section "Generate parent previews index"

---

### Phase 4: Fix API Statistics (Low Risk)

**File:** `src/reporting_tool/statistics.py`

**Change:** Update `write_to_step_summary()` method

**Current Behavior:**

- Returns before completion if no API calls made
- Heading appears but no table (heading written elsewhere)

**New Behavior:**

- Always write table header
- If no calls: write "_No API calls occurred during this run._"
- If calls: write statistics table

**Alternative:** Find and remove where the bare heading appears

---

## Documentation Updates

### Files Already Updated (✅)

- `.github/scripts/README.md` - Updated examples to use `previews`
- `.github/scripts/generate-index.sh` - Updated usage comments

### Files Needing Updates (⏳)

- `IMPLEMENTATION_GUIDE.md` - Update URL examples
- `REPORTING_SYSTEM_OVERVIEW.md` - Update architecture diagrams
- `SETUP.md` - Update GitHub Pages setup instructions
- `README.md` - Update example URLs if present

### New Documentation Created (📄)

- `GITHUB_PAGES_ISSUES_AND_FIXES.md` - Detailed problem analysis
- `PRODUCTION_AT_ROOT_CHANGES.md` - Step-by-step implementation guide
- `IMPLEMENTATION_SUMMARY.md` - This file

---

## Testing Plan

### Pre-Deployment Testing

1. **Review Changes**
   - Review all file changes before committing
   - Verify logic in bash scripts
   - Check for typos in paths

2. **Local Testing (Optional)**
   - Set `GITHUB_REPOSITORY=modeseven-lfit/reporting-tool`
   - Run `generate-index.sh` with test data
   - Verify paths in generated HTML

### Post-Deployment Testing

1. **Preview Workflow Test**
   - Create or update a PR
   - Verify preview generation at `/previews/{pr_number}/`
   - Check parent preview index at `/previews/`
   - Verify all links work

2. **Production Workflow Test**
   - Trigger production workflow manually OR wait for weekly schedule
   - Verify reports at root: `/reporting-tool/onap/report.html`
   - Verify root index lists all projects
   - Check that `previews/` directory not affected

3. **URL Testing**
   - Test all URLs in browser:
     - ✅ `/reporting-tool/` → Production index
     - ✅ `/reporting-tool/onap/report.html` → Production report
     - ✅ `/reporting-tool/previews/` → Preview parent index
     - ✅ `/reporting-tool/previews/6/` → PR #6 preview index
     - ✅ `/reporting-tool/previews/6/onap/report.html` → PR #6 report
   - Verify no 404 errors
   - Verify no broken links in index pages

---

## Migration Strategy

### Zero-Downtime Approach

**Phase 1: Deploy Changes**

- Update workflows and scripts
- Deploy to main branch
- Next workflow runs will use new structure

**Phase 2: Coexistence Period (1-2 weeks)**

- New reports use new structure
- Old reports remain at old URLs
- Both `/production/` and `/previews/` coexist with root-level reports
- Both `/pr-preview/` and `/previews/` coexist

**Phase 3: Cleanup (After Verification)**

- Remove `/production/` directory from gh-pages
- Remove `/pr-preview/` directories from gh-pages
- Update any external documentation
- Complete migration

### Rollback Plan

If issues occur:

1. **Immediate:** Revert commits to main branch
2. **Workflow:** Previous structure still exists in gh-pages
3. **Time to Rollback:** < 5 minutes (git revert + push)
4. **Data Loss:** None (old reports preserved in gh-pages)

---

## Risk Assessment

### Low Risk Changes ✅

- Preview URL rename (`pr-preview` → `previews`)
- Adding parent preview index
- API statistics fix
- Documentation updates

### Medium Risk Changes ⚠️

- Moving production reports to root level
- Updating generate-index.sh logic
- Git add logic changes

### High Risk Changes ❌

- None identified

### Mitigation Strategies

- Test in PR preview before merging
- Watch first production run
- Keep rollback plan ready
- Document all changes thoroughly

---

## Success Criteria

### Functional Requirements

- [ ] All URLs resolve without 404 errors
- [ ] Production reports accessible at `/reporting-tool/{project}/report.html`
- [ ] Preview parent index shows all PR previews
- [ ] Preview reports accessible at `/reporting-tool/previews/{pr}/{project}/report.html`
- [ ] No broken links in any index page
- [ ] API statistics show as expected or display "No API calls" message

### Non-Functional Requirements

- [ ] Page load times < 2 seconds
- [ ] Index pages render as expected on mobile
- [ ] Navigation intuitive and user-friendly
- [ ] No conflicts between production and preview directories

### Documentation Requirements

- [ ] All documentation updated with new URLs
- [ ] Implementation guide available for future reference
- [ ] Testing procedures documented
- [ ] Rollback procedure documented

---

## Timeline

### Estimated Effort

| Task | Effort | Priority |
|------|--------|----------|
| Review changes | 30 min | High |
| Update production workflow | 15 min | High |
| Update generate-index.sh | 30 min | High |
| Add parent preview index | 20 min | High |
| Fix API statistics | 15 min | Medium |
| Documentation updates | 30 min | Medium |
| Testing (manual trigger) | 30 min | High |
| **Total** | **2.5 hours** | |

### Schedule

1. **Day 1:** Apply changes (1.5 hours)
2. **Day 1:** Test with preview PR (30 minutes)
3. **Day 1:** Test with manual production run (30 minutes)
4. **Day 2-7:** Watch scheduled production run
5. **Day 8:** Verify all URLs and cleanup old directories

---

## Dependencies

### Tools Required

- Git access to repository
- GitHub Actions access for manual triggers
- GitHub Pages enabled on repository
- Access to gh-pages branch

### Permissions Required

- Write access to main branch
- Write access to gh-pages branch (via workflow)
- Ability to trigger workflows manually

### External Dependencies

- None (all changes internal)

---

## Open Questions

1. ❓ **Should we add redirects from old URLs?**
   - `/production/onap/` → `/onap/`
   - `/pr-preview/6/` → `/previews/6/`
   - Decision: Not necessary, minimal impact

2. ❓ **How long to keep old directories?**
   - Recommendation: 2 weeks after verification
   - Allows time for any external links to update

3. ❓ **Should we add a sitemap.xml?**
   - Would help with SEO and discovery
   - Future enhancement, not critical

4. ❓ **Should we add search functionality to index pages?**
   - Would improve UX for large number of reports
   - Future enhancement, not critical

---

## Next Steps

### Immediate Actions (Before Commit)

1. ✅ Review all changes in this document
2. ⏳ Review `.github/workflows/reporting-previews.yaml` changes
3. ⏳ Review `.github/workflows/reporting-production.yaml` changes
4. ⏳ Review `.github/scripts/generate-index.sh` changes
5. ⏳ Review `src/reporting_tool/statistics.py` changes
6. ⏳ Create implementation branch
7. ⏳ Apply changes
8. ⏳ Test locally if possible
9. ⏳ Commit with detailed message
10. ⏳ Create pull request
11. ⏳ Test in PR preview environment

### Post-Merge Actions

1. ⏳ Watch first preview generation
2. ⏳ Trigger manual production run for testing
3. ⏳ Verify all URLs work as expected
4. ⏳ Update external documentation
5. ⏳ Schedule cleanup of old directories

---

## Reference Documents

- **GITHUB_PAGES_ISSUES_AND_FIXES.md** - Detailed problem analysis
- **PRODUCTION_AT_ROOT_CHANGES.md** - Step-by-step implementation guide
- **IMPLEMENTATION_SUMMARY.md** - This document

---

## Notes for Implementer

- **DO NOT** commit these changes without review
- Test thoroughly before merging to main
- Consider creating a backup of gh-pages branch
- Watch GitHub Actions workflow runs
- Keep rollback plan accessible
- Document any deviations from this plan

---

## Approval Sign-Off

**Prepared By:** Claude (AI Assistant)
**Date:** 2025-01-19
**Status:** Pending Review

**Reviewed By:** ________________
**Date:** ________________
**Approved:** ☐ Yes  ☐ No  ☐ Changes Required

**Comments:**

```text

---

**Notes:**
- Implementation is ready but NOT committed
- All changes documented in detail
- Ready for your review and manual implementation
- Rollback plan in place if needed
