# Validation and report (read when: the files are written and you validate)

## Run
```bash
node tools/validate-ui-schema/validate.mjs <schema.json> ui-schema/<kind>.json i18n/<kind>/en.json
```
Read only its summary lines. Exit 1 = errors; fix and re-run until 0 errors.

| Output | Meaning | Action |
|---|---|---|
| `ERROR invalid JSON` | file does not parse | fix syntax |
| `ERROR ... scope "..." does not resolve` | scope not in the schema (typo, renamed property) | use the real path; never keep a scope "because it is probably there" |
| `ERROR ... duplicate control for scope` | same property rendered twice in one form | remove one |
| `ERROR ... must point to a leaf property` | rule condition on an object/array | pick the deciding leaf |
| `ERROR ... rule.effect` | not SHOW/HIDE/ENABLE/DISABLE | fix |
| `ERROR ... enumSource.path` | formField path not in the schema | fix or drop and ask |
| `WARNING not covered by any control` | schema property with no control | add the control, or list it as omitted with a reason (server-set, const discriminator, covered by a parent array/oneOf Control) |
| `WARNING i18n: missing "<key>"` | label/title key missing in en.json | add it (rules below) |

Also check by hand: each `x-autoFill` target has a paired rule with the same condition; every permission, enumSource and autoFill value has a source (schema, user, or existing repo file).

## en.json key rules
- `"#.label"` from the root `title`.
- Object root: `"#/properties/<p>.label"`; `.description` only if the schema has a `description`; nested `"#/properties/<p>/properties/<c>.label"`; arrays inside objects `"#/properties/<p>/items/properties/<c>.label"`.
- Array root: item keys are `"#/items/properties/<p>.label"` (root-relative) although Control scopes inside `detail` are `#/properties/<p>`.
- Identity entry for every `Category`/`Group` `label` and every `Label` `text` (key = the exact raw string).
- Skip bare `const` discriminators. Document order. `sv.json`: only from translations the user supplies, same keys.

## Report format
```
Kind: <kind>   Mode: new | update   Root: object | array
Files: ui-schema/<kind>.json, i18n/<kind>/en.json[, sv.json]
Layout: <e.g. Categorization, 5 categories>
Coverage: <covered>/<total> properties; omitted on purpose: <list + reason>
Rules: <n> rules, <n> x-autoFill, <n> enumSource, <n> permission
Validator: <errors> errors, <warnings> warnings (<summary>)
Open questions: <numbered: permissions, enumSource, autoFill values, formats, sv, unsupported features>
Suggested schema improvements: <optional>
```
Worked example of a full pair: `.claude/ui-schema-generator/example/`.
