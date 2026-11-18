# Formats and input options (read when: inspect.mjs lists a format:*, contentEncoding, contentMediaType, longText or array)

| Schema signal | `options` on the Control |
|---|---|
| string with `maxLength` > 200, or name/description says notes, comment, instructions, reason, description | `{ "multi": true }` |
| `format: date` | `{ "format": "date", "saveFormat": "<fmt>", "displayFormat": "<fmt>" }` only when the schema or description names the format (e.g. `DD/MM/YYYY`); otherwise no options |
| `format: date-time` | `{ "saveFormat": "iso" }` (offset kept) or `{ "saveFormat": "iso-utc" }` when the description says UTC; else no options |
| `format: time` | none (time picker) |
| `format: color` | `{ "preview": "color" }` |
| `format: uri` and name/description says image, logo, banner, or `contentMediaType: image/*` | `{ "preview": "image" }` |
| `contentEncoding: base64` and/or `contentMediaType` (file upload; `x-fileExtensions` limits types) | `{ "showFilePreview": true }` for text, PEM and image files |
| array of objects with more than ~3 item fields or conditionals | `{ "detail": { item layout } }`; smaller arrays: no options |
| array of scalars | no options |
| `format: password`, secrets | none; note in the report that masking is unsupported |
| `Group` that holds rarely used settings the user asked to collapse | Group `options: { "defaultExpanded": false }` |
| `format: email`, plain `uri` | none |
