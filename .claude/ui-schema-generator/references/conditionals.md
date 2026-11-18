# Conditionals (read when: inspect.mjs lists if/then/else, dependentRequired, oneOf, anyOf or allOf)

| Schema | UI schema |
|---|---|
| `if` + `then` | `SHOW` rule on the fields that exist only in `then`; condition from `if.properties.<p>` (`const` -> `{ "const": v }`, `enum` -> `{ "enum": [...] }`) |
| `else` | `SHOW` with `{ "not": <if condition> }` on else-only fields (or `HIDE` with the original) |
| `if` with several properties | one `rule` per control, or an `allOf`-style condition `{ "scope": "#", "schema": { ...properties } }` only if a single leaf cannot express it; raise an open question when unsure |
| `dependentRequired` A -> [B] | `SHOW` on B when A is present: strings `{ "type": "string", "minLength": 1 }`, booleans `{ "const": true }`, numbers `{ "type": "number" }` |
| `allOf` of `if/then` blocks (as in loyalty/tax style schemas) | handle each block independently |
| `oneOf` / `anyOf` on a property or items | ONE Control on the property (variant selector). Do not flatten the branches. A `const` discriminator is never a separate control |
| `then` that sets `const`/`default` on another field | candidate `x-autoFill` plus a paired `DISABLE`/`HIDE` rule (see `vocabulary.md`); if unsure, plain rule and an open question |

The `if` property must be a leaf in the same object as the rule target (or reachable by an absolute scope). A condition on an object or array is an error; pick the leaf that decides it or raise an open question.
