# Vocabulary (read when: you start laying out the form)

Only emit what is listed here and in the other references.

## Elements
`Categorization` (root tabs) > `Category` (needs `label`) > `Group` (titled section, `label`) > `HorizontalLayout` / `VerticalLayout` > `Control` (`scope`, `label`). `Label` uses `text`, not `label`. `ListWithDetail` takes `options.detail`.
`Categorization` is valid only at the form root or the root of a root-Control `options.detail`; never nest it.

## Layout choice (object root, first match wins)
1. 3+ logical top-level groups, or 8+ top-level properties: `Categorization`, one `Category` per top-level object or logical group.
2. 3-7 properties incl. 1-2 nested objects: `VerticalLayout` of `Group`s.
3. Flat, 5 or fewer leaves: `VerticalLayout` of `Control`s.

Shared name prefix: same `Group`. Gating boolean first, beside its closest control. 2-3 short fields (codes, ids, numbers, enums) share a `HorizontalLayout`; long text stands alone. Keep schema order unless grouping needs otherwise.

## Array root
```json
{ "type": "Control", "scope": "#", "x-autoFill": [], "options": { "detail": { "type": "VerticalLayout", "elements": [] } } }
```
Layout rules above apply to the item properties inside `detail`. Scopes in `detail` and in `x-autoFill`/`rule` conditions are item-relative (`#/properties/<key>`). `x-autoFill` sits on the outer Control, never inside `detail`.

## Scopes
`#/properties/a/properties/b`, resolved through `$ref` (never write a `$ref` in a scope). A Control on an array property renders add/remove rows; on a `oneOf`/`anyOf` property a variant selector.

## Labels
Schema `title` verbatim, else split camelCase/snake_case to Title Case; 2-4 letter acronyms stay uppercase (`vatID` -> `VAT ID`).

## rule
```json
"rule": { "effect": "SHOW", "condition": { "scope": "#/properties/a", "schema": { "const": true } } }
```
Effects `SHOW`, `HIDE`, `ENABLE`, `DISABLE`. `condition.scope` is a leaf property. SHOW/HIDE affect whether the value is submitted; ENABLE/DISABLE only interactivity. Mapping from schema conditionals: `conditionals.md`.

## x-autoFill
```json
"x-autoFill": [{ "description": "Why", "when": { "scope": "#/properties/a", "schema": { "const": true } }, "set": [{ "scope": "#/properties/b", "value": 0 }] }]
```
Top of an object-root UI schema, or on the root Control for array roots. Edge-triggered: rising edge sets the targets, falling edge removes them, steady state leaves manual edits. Every target needs a paired `rule` with the same condition on its Control (`DISABLE` = visible and enforced, `HIDE` = silently enforced). Emit only when the schema states the value (a `const`/`default` inside a `then`, or a description saying so). Never guess values.

## permission
`"permission": ["<permission.string>"]` on a Control. Only strings the user supplied or that the same kind already uses in this repo; otherwise omit and raise an open question.

## Not supported
Code editor, rich text, slider, icon/image select, tab arrays, submit/action buttons, templating, custom validators, secret masking. Use the plain control and mention it in the report. Do not copy demo content (test-data and error-state categories) from the portal's example form.
