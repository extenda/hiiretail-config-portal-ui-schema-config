"""Builds the che.tender.preview UI schema and the English i18n file from the data schema.

Usage, from the repository root:
    python tools/che.tender.preview/build_ui.py <path to hiiretail-json-schema-registry>/customer-config/checkout-config/che.tender.preview.json

Every setting is offered for every tender type. The type groups the form's rules use (foreign currency for the
currency field, and the type defaults for change and refunds) are read from the schema's $defs, and every label and help text from the schema's titles and descriptions, so rerunning it after
a schema change brings the form in line. Before writing
anything, the script checks that every scope the form uses exists in the schema and that every value a rule
compares with is allowed there, and stops on a miss.
The form has no x-autoFill rules: hidden settings stay in the data and are ignored for types they do not apply to.
"""
import json
import sys
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit(__doc__)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = Path(sys.argv[1])
UI_SCHEMA_PATH = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "ui-schema" / "che.tender.preview.json"
TEXTS_PATH = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "i18n" / "che.tender.preview" / "en.json"

SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
TENDER = SCHEMA["items"]


def fail(message):
    sys.exit(f"Nothing written. {message}")


def kinds_of_group(name):
    """The kinds of a $defs group, which may only name kinds."""
    try:
        group = SCHEMA["$defs"][name]
        group_type = group["properties"]["type"]
        kind = group_type["properties"]["kind"]
    except KeyError:
        fail(f"The schema has no kind group $defs.{name}.")
    unread = ((set(group) - {"$comment", "type", "required", "properties"}) | (set(group["properties"]) - {"type"})
              | (set(group_type) - {"type", "required", "properties"}) | (set(group_type["properties"]) - {"kind"}))
    if unread:
        fail(f"$defs.{name} has conditions the generator does not read: {sorted(unread)}.")
    return kind["enum"] if "enum" in kind else [kind["const"]]


def rounding_methods_with_unit():
    """The rounding methods of the schema rule that requires rounding.precision."""
    for rule in TENDER.get("allOf", []):
        requires_unit = "precision" in rule.get("then", {}).get("properties", {}).get("rounding", {}).get("required", [])
        method = rule.get("if", {}).get("properties", {}).get("rounding", {}).get("properties", {}).get("method", {})
        if requires_unit and "enum" in method:
            return method["enum"]
    fail("The schema has no rule that requires rounding.precision for some rounding methods.")


FOREIGN_CURRENCY = kinds_of_group("kindForeignCurrency")
GIVES_CHANGE_BY_DEFAULT = kinds_of_group("kindGivesChangeByDefault")
REFUNDS_BLOCKED_BY_DEFAULT = kinds_of_group("kindRefundsBlockedByDefault")
ROUNDING_METHODS_WITH_UNIT = rounding_methods_with_unit()
# The overpayment choices that give no change; the Change tab hides its fields for them.
NO_CHANGE = ["EXACT_AMOUNT", "WITHOUT_CHANGE"]

KIND = "#/properties/type/properties/kind"
HARDWARE = "#/properties/type/properties/hardware"
BEHAVIOR = "#/properties/behavior/properties/"
REFUND = "#/properties/refund/properties/"
CHANGE = "#/properties/change/properties/"
LIMITS = "#/properties/limits/properties/"
ROUNDING = "#/properties/rounding/properties/"
IS_ON = {"const": True}
REFUND_CLEARING = "A saved refund amount cannot be cleared yet: Save is then refused."
INTEGRATION = "#/properties/type/properties/integration"
STANDALONE = {"const": "STANDALONE"}


def condition(scope, schema):
    return {"scope": scope, "schema": schema}


def with_rule(element, effect, cond):
    if cond:
        element["rule"] = {"effect": effect, "condition": cond}
    return element


def control(scope, show_if=None, hide_if=None, **options):
    assert not (show_if and hide_if), "an element has one rule"
    element = {"type": "Control", "scope": scope, **options}
    if show_if:
        return with_rule(element, "SHOW", show_if)
    return with_rule(element, "HIDE", hide_if)


def text(content, show_if=None):
    return with_rule({"type": "Label", "text": content}, "SHOW", show_if)


def vertical(elements, show_if=None, hide_if=None):
    assert not (show_if and hide_if), "an element has one rule"
    element = {"type": "VerticalLayout", "elements": elements}
    if show_if:
        return with_rule(element, "SHOW", show_if)
    return with_rule(element, "HIDE", hide_if)


def horizontal(elements):
    return {"type": "HorizontalLayout", "elements": elements}


def category(title, elements, show_if=None):
    return with_rule({"type": "Category", "label": title, "elements": elements}, "SHOW", show_if)


def shown_when_all(element, *conditions):
    """Shows the element only when every condition holds, with one single-condition rule per nested layout.

    Composed conditions are not used, because they are not tried in the Config Portal.
    """
    for cond in reversed(conditions):
        element = vertical([element], show_if=cond)
    return element


def enum_source(url, label_key, secondary_label_key=None):
    source = {"type": "request", "request": {"url": url},
              "response": {"itemsPath": "value", "valueKey": "id", "labelKey": label_key}}
    if secondary_label_key:
        source["display"] = {"secondaryLabelKey": secondary_label_key}
    return {"options": {"enumSource": source}}


# Change and refund settings show only where they take effect: for an explicit choice, or for a type whose type
# default gives change or allows refunds. A choice the user has not made is absent, so it matches no rule value.
def change_fields(show_if=None):
    return vertical([
        text(TENDER["properties"]["change"]["description"]),
        text("A saved amount here cannot be cleared yet: Save is then refused. The alternate change tender list "
             "shows the tenders saved for this target: save a new tender before choosing it here. Choose an "
             "enabled tender, not loyalty points, that allows refunds and has no minimum amounts."),
        control(CHANGE + "tenderId",
                **enum_source("{api:ccc-api}/api/v1/config/che.tender.preview/values/{target.path}", "name",
                              "type.kind")),
        horizontal([control(CHANGE + "threshold"), control(CHANGE + "autoCompleteLimit")]),
    ], show_if=show_if)


def refund_fields(show_if=None, hide_if=None):
    return vertical([
        control(REFUND + "skipAmountPrompt"),
        horizontal([control(REFUND + "maxAmount"), control(REFUND + "minAmount")]),
        text(REFUND_CLEARING),
    ], show_if=show_if, hide_if=hide_if)


detail = {"type": "Categorization", "elements": [
    category("Tender", [
        horizontal([control("#/properties/id"), control("#/properties/name")]),
        control("#/properties/type"),
        control("#/properties/currency", show_if=condition(KIND, {"enum": FOREIGN_CURRENCY}),
                **enum_source("{api:ccc-api}/api/v1/config/cur.currencies.v1/values/{target.path}", "id")),
        text("Choose the tender type first. Every setting left empty uses the default for the type, and each "
             "help text says what that default is. Most saved amounts and choices cannot be cleared: "
             "Save is then refused. To go back to the default, choose the default option where the list has one. "
             "Payment plugins, provider codes and the store currency are added automatically by Store Data."),
        control("#/properties/restrictionRuleId"),
        control("#/properties/description", options={"multi": True}),
        control("#/properties/disabled"),
    ]),
    category("At the Till", [
        control(BEHAVIOR + "defaultTender"),
        # The schema refuses Yes on a cash changer; the note says why before Save is refused.
        shown_when_all(text("A cash changer tender is never the default cash tender: choose Automatic or No."),
                       condition(KIND, {"const": "cash"}),
                       condition(HARDWARE, {"const": "CASH_CHANGER_MACHINE"}),
                       condition(BEHAVIOR + "defaultTender", {"const": "YES"})),
        text("No split payment always takes the exact amount.", show_if=condition(BEHAVIOR + "exclusive", IS_ON)),
        vertical([control(BEHAVIOR + "overpayment")], hide_if=condition(BEHAVIOR + "exclusive", IS_ON)),
        text("This tender was saved with 'Exact Amount Only' on, which this form replaced with 'Overpayment'. While "
             "'Overpayment' is empty it still takes the exact amount: choose an 'Overpayment' option to replace it.",
             show_if=condition(BEHAVIOR + "exactAmountOnly", IS_ON)),
        control(BEHAVIOR + "exclusive"),
        control(BEHAVIOR + "lockTransaction"),
        control(BEHAVIOR + "blockCancel"),
        # The schema refuses both together; the warning says why before Save is refused.
        shown_when_all(
            text("'Lock Sale After Payment Entry' and 'Block Cancelling the Sale' cannot both be on: the sale "
                 "would then be stuck until it is paid in full. Turn one of them off."),
            condition(BEHAVIOR + "lockTransaction", IS_ON),
            condition(BEHAVIOR + "blockCancel", IS_ON)),
        control(BEHAVIOR + "payRemainingAmount"),
        control(BEHAVIOR + "prefillAmount"),
        control(BEHAVIOR + "cashDrawer"),
    ]),
    category("Change", [
        text("No change is given, because 'Overpayment' does not give change.",
             show_if=condition(BEHAVIOR + "overpayment", {"enum": NO_CHANGE})),
        text("No change is given, because 'No Split Payment' always takes the exact amount.",
             show_if=condition(BEHAVIOR + "exclusive", IS_ON)),
        vertical([vertical([
            change_fields(show_if=condition(BEHAVIOR + "overpayment", {"const": "WITH_CHANGE"})),
            vertical([
                change_fields(show_if=condition(KIND, {"enum": GIVES_CHANGE_BY_DEFAULT})),
                vertical([text("With the type default this type takes the exact amount, so no change is given. "
                               "Choose 'Allowed, give change' under 'Overpayment' to set change here.")],
                         hide_if=condition(KIND, {"enum": GIVES_CHANGE_BY_DEFAULT})),
            ], hide_if=condition(BEHAVIOR + "overpayment", {"const": "WITH_CHANGE"})),
        ], hide_if=condition(BEHAVIOR + "exclusive", IS_ON))],
            hide_if=condition(BEHAVIOR + "overpayment", {"enum": NO_CHANGE})),
    ]),
    category("Refunds", [
        vertical([
            text("On cash, change is paid out as a refund: cash always allows refunds, and the maximum refund also "
                 "limits change."),
            control(REFUND + "skipAmountPrompt"),
            control(REFUND + "maxAmount"),
            text(REFUND_CLEARING),
        ], show_if=condition(KIND, {"const": "cash"})),
        vertical([
            control(REFUND + "refundsAllowed"),
            text("This tender was saved with 'Block Refunds' on, which this form replaced with 'Refunds'. While "
                 "'Refunds' is empty, refunds stay blocked: choose a 'Refunds' option to replace it.",
                 show_if=condition(REFUND + "blockRefunds", IS_ON)),
            refund_fields(show_if=condition(REFUND + "refundsAllowed", {"const": "YES"})),
            vertical([
                vertical([
                    refund_fields(hide_if=condition(INTEGRATION, STANDALONE)),
                    text("With the type default a standalone payment does not refund, because nothing checks it. "
                         "Choose 'Allowed' to set refunds here.", show_if=condition(INTEGRATION, STANDALONE)),
                ], hide_if=condition(KIND, {"enum": REFUNDS_BLOCKED_BY_DEFAULT})),
                text("With the type default this type does not refund. Choose 'Allowed' to set refunds here.",
                     show_if=condition(KIND, {"enum": REFUNDS_BLOCKED_BY_DEFAULT})),
            ], hide_if=condition(REFUND + "refundsAllowed", {"enum": ["YES", "NO"]})),
        ], hide_if=condition(KIND, {"const": "cash"})),
    ]),
    category("Limits", [
        text("Leave a limit empty for no limit. A saved limit cannot be cleared yet: Save is then refused."),
        horizontal([control(LIMITS + "maxPerSale"), control(LIMITS + "maxPerEntry")]),
        control(LIMITS + "minPerEntry", hide_if=condition(KIND, {"const": "cash"})),
    ]),
    category("Rounding", [
        text(TENDER["properties"]["rounding"]["description"]),
        horizontal([control(ROUNDING + "method"),
                    control(ROUNDING + "precision",
                            show_if=condition(ROUNDING + "method", {"enum": ROUNDING_METHODS_WITH_UNIT}))]),
    ]),
    category("Advanced", [
        text("Extra attributes are only for settings Extenda Retail support asks you to add. Everything this form "
             "offers must be set in the form, not here."),
        control("#/properties/extraAttributes"),
    ]),
]}
ui_schema = {"type": "ListWithDetail", "scope": "#", "options": {"detail": detail}}


# ---------- Check the form against the schema ----------

def resolve(scope):
    """The schema nodes a scope can point at: a property of the tender, or of one of the type branches."""
    if scope != "#" and not scope.startswith("#/properties/"):
        return []
    nodes = [TENDER]
    for name in scope.split("/properties/")[1:]:
        found = []
        for node in nodes:
            for candidate in [node, *node.get("oneOf", [])]:
                if name in candidate.get("properties", {}):
                    found.append(candidate["properties"][name])
        nodes = found
    return nodes


def allowed_values(field):
    if field.get("type") == "boolean":
        return {True, False}
    values = set(field.get("enum", []))
    values.update(option["const"] for option in field.get("oneOf", []) if "const" in option)
    if "const" in field:
        values.add(field["const"])
    return values


def check_form(element, problems):
    if element.get("scope") and element["scope"] != "#" and not resolve(element["scope"]):
        problems.append(f"no schema field for scope {element['scope']}")
    cond = element.get("rule", {}).get("condition")
    if cond:
        fields = resolve(cond["scope"])
        if not fields:
            problems.append(f"no schema field for rule scope {cond['scope']}")
        else:
            compared = cond["schema"].get("enum", [cond["schema"].get("const")])
            allowed = set().union(*(allowed_values(field) for field in fields))
            problems.extend(f"{value!r} is not a value of {cond['scope']}" for value in compared
                            if value not in allowed)
    for child in element.get("elements", []) + [element.get("options", {}).get("detail", {})]:
        if child:
            check_form(child, problems)


# ---------- Texts from the schema ----------

texts = {"#.label": SCHEMA["title"], "#.description": SCHEMA["description"]}
text_problems = []


def add_text(key, value):
    if texts.setdefault(key, value) != value:
        text_problems.append(f"two different texts for {key}")


# Each type branch gives type.kind its own title, which the branch selector shows; it needs no shared text.
DISCRIMINATOR = "#/items/properties/type/properties/kind"


def collect_texts(node, key):
    if isinstance(node.get("items"), list):
        text_problems.append(f"{key} has a list of item schemas, which the generator does not read")
    for branch in [node, *node.get("oneOf", [])]:
        if "$ref" in branch:
            text_problems.append(f"{key} uses $ref, which the generator does not follow")
        for name, field in branch.get("properties", {}).items():
            field_key = f"{key}/properties/{name}"
            if field_key == DISCRIMINATOR:
                continue
            if "title" in field:
                add_text(f"{field_key}.label", field["title"])
            else:
                text_problems.append(f"{field_key} has no title")
            if "description" in field:
                add_text(f"{field_key}.description", field["description"])
            collect_texts(field, field_key)
    if isinstance(node.get("items"), dict):
        collect_texts(node["items"], f"{key}/items")


collect_texts(TENDER, "#/items")
form_problems = []
check_form(ui_schema, form_problems)
problems = list(dict.fromkeys(form_problems + text_problems))
if problems:
    sys.exit("Nothing written. The form does not match the schema:\n  " + "\n  ".join(problems))


def write(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")


write(UI_SCHEMA_PATH, ui_schema)
write(TEXTS_PATH, texts)
print(f"ui schema and {len(texts)} texts written")
