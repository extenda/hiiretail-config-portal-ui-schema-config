# enumSource (read when: a field's choices must come from an API or from another field of the same form)

Never invent any value here. Use `enumSource` only when the schema (description, `$comment`, an `x-*` keyword) or the user names the source. A field that merely looks like a reference (`storeId`) is an open question: "which endpoint supplies the options for <scope>?".

## request: choices fetched from an API
```json
"options": { "enumSource": {
  "type": "request",
  "request": { "url": "{api:ccc-api}/api/v1/config/che.tender.v2/values/{target.path}", "query": { "type": "PHYSICAL_STORE" } },
  "response": { "itemsPath": "value", "valueKey": "id", "labelKey": "name" },
  "searchable": "auto",
  "display": { "secondaryLabelKey": "businessUnitId", "columns": [{ "key": "softwareId", "label": "Software" }], "responsePreview": true }
} }
```
| Key | Meaning |
|---|---|
| `request.url` | placeholders: `{api:<id>}` registered API base, `{tenantId}`, `{form.<field>}` value of another field (cascading selects), `{target.path}` |
| `request.query` | query parameters |
| `request.auth` | `default` (send the user's token) or `none` (third-party; never send tokens) |
| `request.headerInputs` | user-supplied headers: `{ name, label, description, scheme?, required?, secret? }` |
| `request.fetchOn` | `click` to fetch only when opened (use with headerInputs); `timeoutMs` |
| `response` | `itemsPath` (where the array is, omit if the body is the array), `valueKey`, `labelKey` |
| `searchable` | `"auto"` for long lists |
| `pagination` | `{ type: "page", pageParam, sizeParam, pageSize, firstPage, maxPages }` only when the API pages |
| `display` | `secondaryLabelKey`, `columns [{key,label}]`, `responsePreview` (`true` or `{ "path": "0" }`) |

Only take `valueKey`/`labelKey`/`itemsPath` from the API contract or schema text; if unknown, ask.

## formField: choices from an array elsewhere in the same form
```json
"options": { "enumSource": { "type": "formField", "path": "storeZones", "valueKey": "code", "labelKey": "name" } }
```
Allowed when the schema says the values come from a sibling array. `path` must resolve in the schema (the validator checks it). Without `valueKey`/`labelKey` the array items are used as they are (array of strings).
