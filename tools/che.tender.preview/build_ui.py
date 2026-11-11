"""Builds the che.tender.preview UI schema and the English i18n file from the data schema.

Usage, from the repository root:
    python tools/che.tender.preview/build_ui.py <path to hiiretail-json-schema-registry>/customer-config/checkout-config/che.tender.preview.json

Every kind group in the form's rules is read from the schema's $defs, and every label and help text from the
schema's titles and descriptions, so rerunning it after a schema change brings the form in line.
The form has no x-autoFill rules: hidden settings stay in the data and are ignored for types they do not apply to.
"""
import json
import sys
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit(__doc__)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = Path(sys.argv[1])
UI_OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "ui-schema" / "che.tender.preview.json"
EN_OUT = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "i18n" / "che.tender.preview" / "en.json"

S = json.loads(SCHEMA.read_text(encoding="utf-8"))
D = S["$defs"]


def kinds(name):
    return D[name]["properties"]["type"]["properties"]["kind"]["enum"]


CASH_LIKE = kinds("kindCashLike")
BLOCKABLE = kinds("kindCancelBlockable")
PAY_REMAINING = kinds("kindPayRemaining")
REFUNDABLE = kinds("kindRefundable")
KIND = "#/properties/type/properties/kind"
B = "#/properties/behavior/properties/"
R = "#/properties/refund/properties/"


def rule(effect, scope, schema):
    return {"effect": effect, "condition": {"scope": scope, "schema": schema}}


def ctl(scope, **kw):
    c = {"type": "Control", "scope": scope}
    c.update(kw)
    return c


def label(text, r=None):
    element = {"type": "Label", "text": text}
    if r:
        element["rule"] = r
    return element


def vl(elements, r=None):
    element = {"type": "VerticalLayout", "elements": elements}
    if r:
        element["rule"] = r
    return element


def hl(elements):
    return {"type": "HorizontalLayout", "elements": elements}


def cat(lbl, elements, r=None):
    element = {"type": "Category", "label": lbl, "elements": elements}
    if r:
        element["rule"] = r
    return element


EXACT_ON = {"const": True}

detail = {"type": "Categorization", "elements": [
    cat("Tender", [
        hl([ctl("#/properties/id"), ctl("#/properties/name")]),
        ctl("#/properties/type"),
        ctl("#/properties/currency", rule=rule("SHOW", KIND, {"const": "foreignCurrency"}), options={"enumSource": {
            "type": "request",
            "request": {"url": "{api:ccc-api}/api/v1/config/cur.currencies.v1/values/{target.path}"},
            "response": {"itemsPath": "value", "valueKey": "id", "labelKey": "id"},
        }}),
        label("Choose the tender type first. The other tabs offer only what makes sense for that type, and every "
              "setting left empty uses the default for the type. Most saved amounts and choices cannot be cleared: Save "
              "is then refused. To go back to the default, choose the default option where the list has one. "
              "Payment plugins, provider codes and the store "
              "currency are added automatically by Store Data."),
        ctl("#/properties/restrictionRuleId"),
        ctl("#/properties/description", options={"multi": True}),
        ctl("#/properties/disabled"),
    ]),
    cat("At the Till", [
        ctl(B + "defaultTender"),
        vl([label("A cash changer tender is never the default cash tender: leave this on Automatic or No.",
                  rule("SHOW", "#/properties/type/properties/hardware", {"const": "CASH_CHANGER_MACHINE"}))],
           rule("SHOW", KIND, {"const": "cash"})),
        vl([
            label("No split payment always takes the exact amount.", rule("SHOW", B + "exclusive", EXACT_ON)),
            vl([ctl(B + "exactAmountOnly")], rule("HIDE", B + "exclusive", EXACT_ON)),
        ], rule("SHOW", KIND, {"enum": CASH_LIKE})),
        ctl(B + "exclusive"),
        ctl(B + "lockTransaction"),
        vl([
            ctl(B + "blockCancel", rule=rule("HIDE", "#/properties/type/properties/creditCheck", EXACT_ON)),
            # The schema refuses both together; the warning says why before Save is blocked.
            vl([vl([label("'Lock Sale After Payment Entry' and 'Block Cancelling the Sale' cannot both be on: the "
                          "sale would then be stuck until it is paid in full. Turn one of them off.",
                          rule("SHOW", B + "blockCancel", EXACT_ON))],
                   rule("SHOW", B + "lockTransaction", EXACT_ON))],
               rule("HIDE", "#/properties/type/properties/creditCheck", EXACT_ON)),
        ], rule("SHOW", KIND, {"enum": BLOCKABLE})),
        ctl(B + "payRemainingAmount", rule=rule("SHOW", KIND, {"enum": PAY_REMAINING})),
        ctl(B + "prefillAmount"),
        ctl(B + "cashDrawer"),
    ]),
    cat("Change", [
        label("No change is given, because the tender takes the exact amount.",
              rule("SHOW", B + "exactAmountOnly", EXACT_ON)),
        label("No change is given, because 'No Split Payment' always takes the exact amount.",
              rule("SHOW", B + "exclusive", EXACT_ON)),
        vl([vl([
            label("Leave everything empty to give all change in the store's default cash tender. The alternate "
                  "change tender list shows the tenders saved for this target: save a new tender before choosing "
                  "it here, and choose a cash, foreign currency, gift certificate or voucher tender."),
            ctl("#/properties/change/properties/tenderId", options={"enumSource": {
                "type": "request",
                "request": {"url": "{api:ccc-api}/api/v1/config/che.tender.preview/values/{target.path}"},
                "response": {"itemsPath": "value", "valueKey": "id", "labelKey": "name"},
                "display": {"secondaryLabelKey": "type.kind"},
            }}),
            hl([ctl("#/properties/change/properties/threshold"),
                ctl("#/properties/change/properties/autoCompleteLimit")]),
        ], rule("HIDE", B + "exclusive", EXACT_ON))], rule("HIDE", B + "exactAmountOnly", EXACT_ON)),
    ], rule("SHOW", KIND, {"enum": CASH_LIKE})),
    cat("Refunds", [
        label("Standalone mobile payments cannot be refunded at the till: a mobile refund needs the original app payment.",
              rule("SHOW", "#/properties/type/properties/integration", {"const": "STANDALONE"})),
        vl([
            label("On cash, change is paid out as a refund: cash always allows refunds, and the maximum refund also "
                  "limits change."),
            ctl(R + "skipAmountPrompt"),
            ctl(R + "maxAmount"),
        ], rule("SHOW", KIND, {"const": "cash"})),
        vl([vl([
            ctl(R + "blockRefunds"),
            vl([
                ctl(R + "skipAmountPrompt"),
                hl([ctl(R + "maxAmount"), ctl(R + "minAmount")]),
            ], rule("HIDE", R + "blockRefunds", EXACT_ON)),
        ], rule("HIDE", KIND, {"const": "cash"}))],
            rule("HIDE", "#/properties/type/properties/integration", {"const": "STANDALONE"})),
    ], rule("SHOW", KIND, {"enum": REFUNDABLE})),
    cat("Limits", [
        label("Leave a limit empty for no limit."),
        hl([ctl("#/properties/limits/properties/maxPerSale"),
            ctl("#/properties/limits/properties/maxPerEntry")]),
        ctl("#/properties/limits/properties/minPerEntry", rule=rule("HIDE", KIND, {"const": "cash"})),
    ]),
    cat("Rounding", [
        label("Leave empty, or choose 'No rounding', for no rounding. Choose a method and the smallest coin in use to round amounts paid "
              "with this tender."),
        hl([ctl("#/properties/rounding/properties/method"),
            ctl("#/properties/rounding/properties/precision",
                rule=rule("SHOW", "#/properties/rounding/properties/method",
                          {"enum": ["MATHEMATICAL", "ROUND_HALF_DOWN"]}))]),
    ], rule("SHOW", KIND, {"enum": CASH_LIKE})),
    cat("Advanced", [
        label("Extra attributes are only for settings Extenda Retail support asks you to add. Everything this form "
              "offers must be set in the form, not here."),
        ctl("#/properties/extraAttributes"),
    ]),
]}


def write(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


write(UI_OUT, {"type": "ListWithDetail", "scope": "#", "options": {"detail": detail}})

items = S["items"]
en = {"#.label": S["title"], "#.description": S["description"]}


def walk(props, prefix):
    for k, p in props.items():
        key = f"{prefix}/properties/{k}"
        if "title" in p:
            en[f"{key}.label"] = p["title"]
        if "description" in p:
            en[f"{key}.description"] = p["description"]
        if p.get("type") == "object" and "properties" in p:
            walk(p["properties"], key)


walk(items["properties"], "#/items")
for branch in items["properties"]["type"]["oneOf"]:
    for k, p in branch["properties"].items():
        if k == "kind":
            continue
        key = f"#/items/properties/type/properties/{k}"
        en.setdefault(f"{key}.label", p["title"])
        if "description" in p:
            en.setdefault(f"{key}.description", p["description"])
for k, p in items["properties"]["extraAttributes"]["items"]["properties"].items():
    key = f"#/items/properties/extraAttributes/items/properties/{k}"
    en[f"{key}.label"] = p["title"]
    if "description" in p:
        en[f"{key}.description"] = p["description"]
write(EN_OUT, en)
print("ui schema written; i18n keys:", len(en))
