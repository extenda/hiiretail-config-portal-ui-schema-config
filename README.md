# HiiRetail Config Portal - UI Schema Config

This repository contains configuration files used by the HiiRetail Config Portal. Below is a description of each folder and its purpose.

## Folders

### `ui-schema`

Contains JSON Forms configuration files that define the UI schema and data schema for dynamic form rendering. These files control the structure, layout, and validation rules of forms across the portal.

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

### `i18n`

Contains internationalization (i18n) message files for different languages. Each file provides translated strings used throughout the portal, enabling multi-language support for end users.

### `theme`

Contains theme configuration files for different tenants. Each tenant can have its own theme definition (colors, typography, branding, etc.), allowing the portal to be white-labeled and customized per tenant.

### `tools`

Generators for forms that are built from their data schema instead of written by hand.

`tools/che.tender.preview/build_ui.py` writes `ui-schema/che.tender.preview.json` and `i18n/che.tender.preview/en.json` from the tender schema in hiiretail-json-schema-registry. Labels, help texts and the type groups the form's rules use all come from that schema, so change the schema first and then run, from the repository root:

```bash
python tools/che.tender.preview/build_ui.py ../hiiretail-json-schema-registry/customer-config/checkout-config/che.tender.preview.json
```

Do not edit the two generated files by hand: the next run overwrites them.
