# HiiRetail Config Portal - UI Schema Config

This repository contains configuration files used by the HiiRetail Config Portal. Below is a description of each folder and its purpose.

## Folders

### `ui-schema`

Contains JSON Forms configuration files that define the UI schema and data schema for dynamic form rendering. These files control the structure, layout, and validation rules of forms across the portal.

Portal options for secrets (any kind, no portal code per kind):

| Option | Where | Effect |
|---|---|---|
| `"mask": true` | `Control` | The value is shown as dots, also in the review and data preview dialogs. Fields with `writeOnly: true` or `format: "password"` in the kind schema are masked without it; `"mask": false` turns that off. Use the option when `format` is already taken (e.g. `uuid`). |
| `"viewable": true` | `Control` | Adds an eye button to a masked field so the user can show the value. Without it a masked field stays dots. |
| `"elementLabelProp": "name"` or `["name", "code"]` | array `Control`, `ListWithDetail` | Titles each item with that item property (dot paths allowed; with a list, the first non-empty one). Items without a value keep the default title, e.g. "Terminals 2". |
| `"editGuard": true` | `Control` | Once the field has a saved value it is read-only, with an Edit button (Cancel puts the value back). On by default for masked fields; `"editGuard": false` turns it off. A masked field starts empty when edited and keeps the saved secret until something is typed. |
| `"type": "Action"` | element | A button that opens a portal-registered dialog. Needs `"action"` (id of a dialog registered in the portal, e.g. `generateValues`), `"label"` and `"params"` (object read by that action). `generateValues` params: `title`, `note`, `fields[]` of `{ scope, label, generator: "uuid", displayPrefix? }`; "Send values to fields" writes each generated value into its scope (displayPrefix is display only). `"options": { "placement": "header" }` puts the button right-aligned in the header of the `Group` it sits in (it does not toggle the group); without it the button is inline. An id the portal does not know renders a disabled button. Labels, title and note are i18n raw-text keys. |

An optional object (not in its parent's `required`) is either all empty or complete: when all its fields are cleared it is saved with empty strings and shows no errors; once one field has a value, its mandatory fields apply. The portal also prefills fields that have a schema `default` when no value is set. `tools/validate-ui-schema` checks these options.

### `navigationbar`

Contains JSON configuration files that define the structure and items of the navigation bar. This allows the navigation menu to be customized and managed without code changes.

`navigation.json` holds a `navigation` array of items. Every item has `id`, `label`, `type` and `order`, an optional `icon`, and one of these types:

| `type` | Extra fields | Renders |
|---|---|---|
| `group` | `children` (items) | A collapsible section |
| `kind` | `path` (`/<kind id>`) | The JSON Forms editor for that CCC kind |
| `app` | `appId`, optional `permissions` (string array) | A custom UI app registered in configuration-portal's child-app registry under `appId` |

An `app` item shows only when configuration-portal (hiiretail-frontend) has an app registered under its `appId`; otherwise the item is dropped. The user needs both the app's own permissions and the item's `permissions`. The legacy configuration portal ignores `app` items.

```json
{ "id": "pos-config", "label": "POS config", "type": "app", "appId": "pos-config", "order": 0, "permissions": ["ccc.configuration.get"] }
```

A `kind` or `group` item can have an optional `rule` that greys out (`DISABLE`, the default) or removes (`HIDE`) the item when a field of another kind, resolved at the level selected in the target finder, is not one of the allowed values. The effect names are the same as in UI schema rules. `field` is a dot path into the resolved value, and `in` lists the allowed values. The children of a group follow the group. While the value is loading, or when it can't be read, the item stays enabled. The sidebar follows the saved value, not unsaved edits in an open form. Configuration-portal (hiiretail-frontend) applies rules; until it supports them, they are ignored.

```json
{ "id": "cpy-adyen-cloud", "label": "Adyen cloud", "type": "group", "order": 1, "children": [], "rule": { "effect": "DISABLE", "condition": { "kind": "cpy.payment-router-card.v2", "field": "connector", "in": ["ADYEN_CLOUD"] } } }
```

### `i18n`

Contains internationalization (i18n) message files for different languages. Each file provides translated strings used throughout the portal, enabling multi-language support for end users.

### `theme`

Contains theme configuration files for different tenants. Each tenant can have its own theme definition (colors, typography, branding, etc.), allowing the portal to be white-labeled and customized per tenant.

### `tools`

Generators for forms that are built from their data schema instead of written by hand.

`tools/che.tender.preview/build_ui.py` writes `ui-schema/che.tender.preview.json` and `i18n/che.tender.preview/en.json` from the tender schema in hiiretail-json-schema-registry. Labels, help texts and the foreign currency group the currency field uses all come from that schema, so change the schema first and then run, from the repository root:

```bash
python tools/che.tender.preview/build_ui.py ../hiiretail-json-schema-registry/customer-config/checkout-config/che.tender.preview.json
```

Do not edit the two generated files by hand: the next run overwrites them.

`tools/validate-ui-schema/validate.mjs` checks any UI schema against the JSON Schema of its kind (see [Review and validate](#4-review-and-validate-the-output)); `tools/validate-ui-schema/inspect.mjs` prints a compact outline of a JSON Schema (used by the agent to avoid reading large schemas whole). It has no dependencies, only Node 18+.

## Getting a PR ready for a new schema (UI schema agent)

**In short.** `ui-schema-generator` is a Claude Code agent that turns a kind's JSON Schema (a local file or a GitHub link) into `ui-schema/<kind>.json` and `i18n/<kind>/en.json`, validates them, and reports coverage and open questions. You review the draft, open a PR.

**Quick start** (details below):

```bash
git clone https://github.com/extenda/hiiretail-config-portal-ui-schema-config && cd hiiretail-config-portal-ui-schema-config
git checkout -b feat/<TICKET>-ui-schema-<kind>
claude        # then:  Use the ui-schema-generator agent on <local path | GitHub link>
node tools/validate-ui-schema/validate.mjs <schema.json> ui-schema/<kind>.json i18n/<kind>/en.json
```

Then answer the agent's open questions, commit, push and open the PR ([section 9](#9-branch-commit-and-pr)).

### Contents

1. [What the agent is and why it exists](#1-what-the-agent-is-and-why-it-exists)
2. [Prerequisites](#2-prerequisites)
3. [Step by step](#3-step-by-step)
4. [Review and validate the output](#4-review-and-validate-the-output)
5. [Inputs, outputs and naming](#5-inputs-outputs-and-naming)
6. [What the agent can generate](#6-what-the-agent-can-generate)
7. [Conditionals, and what the agent will not invent](#7-conditionals-and-what-the-agent-will-not-invent)
8. [Worked example](#8-worked-example)
9. [Branch, commit and PR](#9-branch-commit-and-pr)
10. [Troubleshooting and FAQ](#10-troubleshooting-and-faq)
11. [How the agent is built, changing it, getting help](#11-how-the-agent-is-built-changing-it-getting-help)

### 1. What the agent is and why it exists

Every configuration kind in the portal (for example `che.tender.v2`) has a JSON Schema in `hiiretail-json-schema-registry` that describes the data. The portal renders its form with JSON Forms, which also needs a **UI schema** (layout, grouping, conditional visibility, special inputs) and a label file (`i18n/<kind>/en.json`). Writing these by hand is slow and error-prone: a wrong scope silently renders nothing, a missing i18n key shows a raw path.

The agent ([`.claude/agents/ui-schema-generator.md`](.claude/agents/ui-schema-generator.md), a [Claude Code subagent](https://docs.claude.com/en/docs/claude-code/sub-agents)) reads the schema (resolving `$ref`/`$defs`, `oneOf`/`anyOf`, `if`/`then`/`else`, arrays, enums), writes the two files following this repo's conventions, validates its own output with a script until there are no errors, and ends with a **coverage report** and **open questions** for things only a human can decide. It produces a first draft to be reviewed. It never edits the JSON Schema or other kinds, and never commits or opens the PR.

### 2. Prerequisites

| Need | How to check |
|---|---|
| [Claude Code](https://docs.claude.com/en/docs/claude-code/overview), logged in | `claude --version` |
| Node 18+ (validator and inspector scripts, no dependencies) | `node -v` |
| GitHub CLI, authenticated | `gh auth status` |
| Read access to the repo holding the schema (usually `extenda/hiiretail-json-schema-registry`, private) | open the link in a browser, or `gh api repos/<owner>/<repo>` |
| Push access to this repo | you can create a branch and PR here |
| A clone of this repo as the working directory | the agent is found automatically from `.claude/agents/` when `claude` starts in the repo root |

The agent reads private schemas through `gh api`: the access you have through `gh` is the access it has. If `gh` asks for more scopes: `gh auth refresh -s repo` (and authorize the token for the org if it uses SSO).

### 3. Step by step

1. Start from an up-to-date `master` and create the branch ([section 9](#9-branch-commit-and-pr)).
2. Start Claude Code in the repo root: `claude`.
3. Invoke the agent. Local file:
   ```text
   Use the ui-schema-generator agent to build the UI schema for ~/work/schemas/che.gift-card.v1.json
   ```
   GitHub link (blob or raw URL, any branch, tag or SHA; private repos work through your `gh` login):
   ```text
   Use the ui-schema-generator agent on https://github.com/extenda/hiiretail-json-schema-registry/blob/master/customer-config/checkout-config/che.gift-card.v1.json
   ```
   You can add details in the same sentence: the kind id if it differs from the file name (`kind: che.gift-card.v1`), permission strings per field, date formats, the API behind a dropdown, or translations for `sv.json`. Non-interactive: `claude -p "Use the ui-schema-generator agent on <path or link>"`.
4. Read the report ([section 4](#4-review-and-validate-the-output)); answer the open questions and ask for adjustments ("put pricing fields in their own category", "guard `maxAmount` with permission X").
5. Re-run the validator yourself, look at the form in the preview, then commit, push and open the PR ([section 9](#9-branch-commit-and-pr)).

Updating an existing kind works the same way: pass the new schema version. The agent sees the existing files, keeps valid labels, groups and permissions, and changes only what the schema change requires.

### 4. Review and validate the output

**Coverage report.** The agent ends with:

```text
Kind: che.gift-card.v1   Mode: new   Root: object
Files: ui-schema/che.gift-card.v1.json, i18n/che.gift-card.v1/en.json
Layout: VerticalLayout, 1 Group
Coverage: 6/6 properties; omitted on purpose: none
Rules: 1 rule, 0 x-autoFill, 0 enumSource, 0 permission
Validator: 0 errors, 0 warnings
Open questions: 1. Which permission should guard "maxAmount"?
```

- **Coverage**: schema properties with a control. Anything omitted must be listed with a reason (server-set field, constant discriminator). An omission without a reason is a bug: ask the agent.
- **Rules / autoFill / enumSource / permission**: compare with the schema; every `if`/`then` and `dependentRequired` should appear as a rule.
- **Open questions**: each is something the agent refused to guess. Resolve all, or list them in the PR.

**Validate yourself:**

```bash
node tools/validate-ui-schema/validate.mjs <schema.json> ui-schema/<kind>.json i18n/<kind>/en.json
```

Errors (exit code 1) must be fixed: invalid JSON, a scope that does not exist in the schema, two controls for one scope, a rule condition on an object or array, an unresolved `enumSource.path`. Warnings (properties no control covers, missing i18n keys) must be fixed or justified in the PR. The full table of messages is in [`validation.md`](.claude/ui-schema-generator/references/validation.md).

**Look at the form.** Paste the schema and UI schema into the portal's JSON Forms preview (Configuration Portal, in `hiiretail-frontend`) and click through: every field is there, conditional fields show and hide as the schema says, required fields validate, arrays add and remove rows.

### 5. Inputs, outputs and naming

| Input | Accepted forms |
|---|---|
| Schema | local path; GitHub `blob` URL; `raw.githubusercontent.com` URL; any ref (branch, tag, SHA) |
| Kind id | optional; defaults to the schema file name without `.json`; pattern `<domain>.<name>.<vN>`, e.g. `che.gift-card.v1` |
| Extras | permissions, formats, enum sources, translations (otherwise they become open questions) |

| Output | Location |
|---|---|
| UI schema | `ui-schema/<kind>.json` |
| English labels and descriptions | `i18n/<kind>/en.json` |
| Swedish (optional) | `i18n/<kind>/sv.json`, only from translations you provide |

Nothing else is written. Fetched schemas go to a temporary folder. Registering the kind in `navigationbar/navigation.json`, if needed, is a manual follow-up the agent reports.

### 6. What the agent can generate

Layouts (`Categorization` > `Category` > `Group` > `HorizontalLayout`/`VerticalLayout` > `Control`), array forms (`options.detail`), `rule` (`SHOW`/`HIDE`/`ENABLE`/`DISABLE`), `x-autoFill`, `permission`, and `options` for long text, dates, colors, images, files, collapsed groups and dynamic choices (`enumSource`: `request` and `formField`). It picks the layout by size: 3+ groups or 8+ properties give tabs, a few properties with a nested object give groups, small flat schemas a plain list; short related fields share a row.

The full vocabulary with examples is kept in the agent's reference files (the agent loads only the ones a schema needs):

| Topic | File |
|---|---|
| Layouts, labels, rule, x-autoFill, permission, array roots, unsupported features | [`vocabulary.md`](.claude/ui-schema-generator/references/vocabulary.md) |
| `if`/`then`/`else`, `dependentRequired`, `oneOf`/`anyOf` | [`conditionals.md`](.claude/ui-schema-generator/references/conditionals.md) |
| dates, files, color, image, long text, array options | [`formats.md`](.claude/ui-schema-generator/references/formats.md) |
| `enumSource` (`request`, `formField`) | [`enum-source.md`](.claude/ui-schema-generator/references/enum-source.md) |
| validator messages, en.json keys, report format | [`validation.md`](.claude/ui-schema-generator/references/validation.md) |

### 7. Conditionals, and what the agent will not invent

| Schema says | Agent writes |
|---|---|
| `if` / `then` | `SHOW` rule on the fields only present in `then` |
| `else` | `SHOW` with the negated condition, or `HIDE` with the original |
| `dependentRequired` (A needs B) | `SHOW` rule on B when A is set |
| `oneOf` / `anyOf` property | one control (the portal renders a variant selector) |
| a value stated in the schema | optional `x-autoFill` plus a paired rule |

It does **not** invent, and instead lists under open questions: permission strings (unless you gave them or the kind already has them), `enumSource` URLs and API ids, `x-autoFill` values, date formats the schema does not name, Swedish translations, and anything the portal cannot render (code editor, rich text, slider, submit buttons, secret masking). It never copies demo-only content from the portal's example form.

### 8. Worked example

Input [`che.gift-card.v1.schema.json`](.claude/ui-schema-generator/example/che.gift-card.v1.schema.json): six properties, one nested `expiry` object with `dependentRequired: { expires: [months] }`, one long text field.

Output [`che.gift-card.v1.ui-schema.json`](.claude/ui-schema-generator/example/che.gift-card.v1.ui-schema.json) and [`che.gift-card.v1.en.json`](.claude/ui-schema-generator/example/che.gift-card.v1.en.json):

- six properties, one nested object: a `VerticalLayout` with a `HorizontalLayout` per related pair and one `Group` ("Expiry");
- `months` gets `"rule": { "effect": "SHOW", "condition": { "scope": "#/properties/expiry/properties/expires", "schema": { "const": true } } }` because of `dependentRequired`;
- `terms` (`maxLength` 1000) gets `"options": { "multi": true }`;
- `en.json` has `#.label`, a `.label` per property, `.description` where the schema has one, and the identity entry `"Expiry": "Expiry"` for the group title.

Check it yourself:

```bash
node tools/validate-ui-schema/validate.mjs .claude/ui-schema-generator/example/che.gift-card.v1.schema.json \
  .claude/ui-schema-generator/example/che.gift-card.v1.ui-schema.json .claude/ui-schema-generator/example/che.gift-card.v1.en.json
# 0 error(s), 0 warning(s)
```

### 9. Branch, commit and PR

- **Branch**: `feat/<TICKET>-ui-schema-<kind>` from an up-to-date `master`, e.g. `feat/HCC-1234-ui-schema-che.gift-card.v1` (`fix/...` for corrections only).
- **Commit** (one per kind, Conventional Commits with the Jira key as in this repo's history): `feat(<TICKET>): Add UI schema for <kind>` (`fix(<TICKET>): ...` for corrections). Stage only this kind's files:
  ```bash
  git add ui-schema/<kind>.json i18n/<kind>/
  git commit -m "feat(HCC-1234): Add UI schema for che.gift-card.v1"
  git push -u origin HEAD
  ```
- **PR**: base `master`, title equal to the commit. Description: link to the JSON Schema with the commit SHA it was read from, the agent's coverage report, how you verified (validator, preview) and the resolved open questions. `gh pr create --base master` or the browser.

PR checklist (copy into the description):

```markdown
- [ ] Schema source and commit SHA linked
- [ ] `validate.mjs` reports 0 errors; every warning fixed or explained
- [ ] Coverage report pasted; every omitted property has a reason
- [ ] All open questions resolved (permissions, enumSource, autoFill, formats) or listed as follow-ups
- [ ] Form checked in the JSON Forms preview (fields, conditionals, required, arrays)
- [ ] `en.json` complete; `sv.json` added or explicitly deferred
- [ ] Only `ui-schema/<kind>.json` and `i18n/<kind>/` changed (plus navigation if needed)
- [ ] Commit and PR title follow `feat(<TICKET>): ...`
```

### 10. Troubleshooting and FAQ

| Problem | What to do |
|---|---|
| "Agent not found" | Start `claude` from the repo root; `/agents` should list `ui-schema-generator`. |
| 404 or 403 on a GitHub link | `gh auth status`; confirm you can open the link; `gh auth refresh -s repo`; authorize the token for the org (SSO). |
| Branch name with slashes in the link | Use a raw URL or the commit SHA. |
| Validator: `scope ... does not resolve` | The schema changed or the agent mistyped. Re-run the agent on the current schema and paste the error. |
| Validator warns about uncovered properties | Ask the agent to cover them, or keep a written reason per omission in the PR. |
| Label missing or a raw path shows in the portal | The `en.json` key is missing or mis-prefixed. Array-root schemas use `#/items/properties/...` for labels but `#/properties/...` for scopes. |
| I need a permission or an API-backed dropdown | Tell the agent the permission string, or the exact endpoint plus `valueKey`/`labelKey`; it will not guess. |
| The schema has no `title`/`description` | Labels derive from property names and descriptions are absent. Improving the schema beats hand-editing the output; then re-run. |
| I hand-edited and want to regenerate | A re-run on an existing kind is an update that keeps valid labels, groups, permissions; review the diff. Kinds with their own generator in `tools/` (`che.tender.preview`) use that. |
| Output differs between runs | Layout is a judgement call. Ask for the grouping you want; the validator guarantees correctness, not taste. |

### 11. How the agent is built, changing it, getting help

The agent loads in layers to keep token use low: the agent file is a short workflow, the scripts summarise the schema and the output so the whole file is never read, and each reference file is read only when the schema needs that feature.

| Piece | Path |
|---|---|
| Agent (workflow, hard rules) | `.claude/agents/ui-schema-generator.md` |
| Reference files, one worked example | `.claude/ui-schema-generator/references/`, `.claude/ui-schema-generator/example/` |
| Schema outline / subtree viewer | `tools/validate-ui-schema/inspect.mjs` |
| Output validator | `tools/validate-ui-schema/validate.mjs` |

When the portal gains a UI-schema feature, update the matching reference file (and the validator if it can be checked statically) in the same PR as the portal change. To propose a change or report a wrong output, open an issue or a PR in this repository with the schema link, what the agent produced and what you expected; keep agent changes small and show a before/after example.
