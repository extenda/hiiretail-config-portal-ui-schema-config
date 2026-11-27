#!/usr/bin/env node
// Validates a UI schema against the JSON schema of its kind.
// Usage: node tools/validate-ui-schema/validate.mjs <schema.json> <ui-schema.json> [i18n/<kind>/en.json]
// Exit code 0 = no errors (coverage gaps and missing translations are listed as warnings), 1 = errors.
import { readFileSync } from 'node:fs';

const [schemaPath, uiPath, i18nPath] = process.argv.slice(2);
if (!schemaPath || !uiPath) {
  console.error('Usage: validate.mjs <schema.json> <ui-schema.json> [en.json]');
  process.exit(2);
}
const load = (p) => JSON.parse(readFileSync(p, 'utf8'));
const errors = [];
const warnings = [];
let root;
let ui;
let i18n;
try {
  root = load(schemaPath);
  ui = load(uiPath);
  i18n = i18nPath ? load(i18nPath) : null;
} catch (e) {
  console.error(`ERROR invalid JSON: ${e.message}`);
  process.exit(1);
}

const deref = (node, seen = new Set()) => {
  while (node && typeof node.$ref === 'string') {
    if (seen.has(node.$ref)) return node;
    seen.add(node.$ref);
    const target = node.$ref.replace(/^#\/?/, '').split('/').filter(Boolean)
      .reduce((n, k) => (n ? n[k] : undefined), root);
    if (!target) return undefined;
    node = target;
  }
  return node;
};

// Branch schemas whose properties are reachable from `node` (oneOf/anyOf/allOf/then/else).
const branches = (node) => {
  const n = deref(node);
  if (!n) return [];
  const out = [n];
  for (const k of ['allOf', 'oneOf', 'anyOf']) for (const b of n[k] ?? []) out.push(...branches(b));
  for (const k of ['then', 'else']) if (n[k]) out.push(...branches(n[k]));
  return out;
};

const child = (node, key) => {
  for (const b of branches(node)) if (b.properties && key in b.properties) return deref(b.properties[key]);
  return undefined;
};

// Resolve a "#/properties/a/properties/b" scope; "items" segments are followed too.
const resolve = (ctx, scope) => {
  if (scope === '#') return ctx;
  const parts = scope.replace(/^#\//, '').split('/');
  let node = ctx;
  for (let i = 0; i < parts.length && node; i++) {
    if (parts[i] === 'properties') node = child(node, parts[++i]);
    else if (parts[i] === 'items') node = deref(deref(node)?.items);
    else return undefined;
  }
  return node;
};

const leafPointers = (ctx, prefix = '#', depth = 0) => {
  const out = [];
  if (depth > 6) return out;
  const seen = new Set();
  for (const b of branches(ctx)) {
    for (const [k, v] of Object.entries(b.properties ?? {})) {
      if (seen.has(k)) continue;
      seen.add(k);
      const p = `${prefix}/properties/${k}`;
      const n = deref(v);
      if (n && n.type === 'object' && n.properties) out.push(...leafPointers(n, p, depth + 1));
      else out.push(p);
    }
  }
  return out;
};

const covered = new Set();
const checkScope = (ctx, scope, where) => {
  if (typeof scope !== 'string' || !scope.startsWith('#')) {
    errors.push(`${where}: scope "${scope}" is not a JSON pointer starting with #`);
    return undefined;
  }
  const node = resolve(ctx, scope);
  if (!node) errors.push(`${where}: scope "${scope}" does not resolve in the schema`);
  return node;
};

const walk = (el, ctx, path, ctxId, seenControls) => {
  if (!el || typeof el !== 'object') return;
  const here = `${path}${el.type ? `<${el.type}>` : ''}`;
  if (el.rule) {
    const cs = el.rule.condition?.scope;
    const target = checkScope(ctx, cs, `${here} rule.condition`);
    if (target && (target.type === 'object' || target.type === 'array')) {
      errors.push(`${here}: rule.condition.scope "${cs}" must point to a leaf property`);
    }
    if (!['SHOW', 'HIDE', 'ENABLE', 'DISABLE'].includes(el.rule.effect)) {
      errors.push(`${here}: rule.effect "${el.rule.effect}" is not SHOW/HIDE/ENABLE/DISABLE`);
    }
  }
  const elp = el.options?.elementLabelProp;
  if (elp !== undefined) {
    const paths = Array.isArray(elp) ? elp : [elp];
    if (paths.length === 0 || paths.some((p) => typeof p !== 'string' || p.trim() === '')) {
      errors.push(`${here}: options.elementLabelProp must be a property path or a list of them`);
    }
  }
  for (const flag of ['mask', 'editGuard', 'viewable', 'deletable']) {
    if (el.options?.[flag] !== undefined && typeof el.options[flag] !== 'boolean') {
      errors.push(`${here}: options.${flag} must be true or false`);
    }
  }
  if (el.type === 'Action') {
    if (typeof el.action !== 'string' || el.action === '') errors.push(`${here}: Action needs an "action" id (string)`);
    const placement = el.options?.placement;
    if (placement !== undefined && placement !== 'header') {
      errors.push(`${here}: Action options.placement must be "header" (or omitted for inline)`);
    }
    if (el.params === null || typeof el.params !== 'object' || Array.isArray(el.params)) {
      errors.push(`${here}: Action needs "params" (object)`);
    } else {
      for (const [i, f] of (el.params.fields ?? []).entries()) {
        checkScope(ctx, f?.scope, `${here} params.fields[${i}]`);
        covered.add(`${ctxId}|${f?.scope}`);
      }
    }
    return;
  }
  if (el.type === 'Control') {
    const node = checkScope(ctx, el.scope, here);
    const key = `${ctxId}|${el.scope}`;
    if (seenControls.has(key)) errors.push(`${here}: duplicate control for scope "${el.scope}"`);
    seenControls.add(key);
    covered.add(key);
    const es = el.options?.enumSource;
    if (es?.type === 'formField' && typeof es.path === 'string') {
      const formPath = `#/properties/${es.path.split('.').join('/properties/')}`;
      if (!resolve(ctx, formPath) && !resolve(deref(root.type === 'array' ? root.items : root), formPath)) {
        errors.push(`${here}: enumSource.path "${es.path}" does not resolve in the schema`);
      }
    }
    if (el.options?.detail && node) {
      const detailCtx = node.type === 'array' ? deref(node.items) : node;
      const id = `${ctxId}>${el.scope}`;
      walk(el.options.detail, detailCtx, `${here}.detail`, id, new Set());
    }
    return;
  }
  for (const [i, c] of (el.elements ?? []).entries()) walk(c, ctx, `${here}[${i}]`, ctxId, seenControls);
};

// x-autoFill scopes live at the top of the UI schema (object root) or on the root Control (array root).
const checkAutoFill = (rules, ctx, where) => {
  for (const [i, r] of (rules ?? []).entries()) {
    checkScope(ctx, r.when?.scope, `${where}.x-autoFill[${i}].when`);
    for (const s of r.set ?? []) checkScope(ctx, s.scope, `${where}.x-autoFill[${i}].set`);
  }
};

const rootCtx = deref(root);
const seen = new Set();
walk(ui, rootCtx, 'root', 'root', seen);
const detailCtx = ui.type === 'Control' && ui.scope === '#' && ui.options?.detail
  ? (rootCtx.type === 'array' ? deref(rootCtx.items) : rootCtx) : rootCtx;
checkAutoFill(ui['x-autoFill'], detailCtx, 'root');

// Coverage: leaf properties of the form root not reached by any Control (a Control on an ancestor covers its subtree).
const isCovered = (ctxId, p, ctxScopes) => ctxScopes.some((s) => s === '#' || p === s || p.startsWith(`${s}/`));
const scopesFor = (id) => [...covered].filter((k) => k.startsWith(`${id}|`)).map((k) => k.slice(id.length + 1));
let formCtx = rootCtx;
let formId = 'root';
if (ui.type === 'Control' && ui.scope === '#' && ui.options?.detail) {
  formCtx = rootCtx.type === 'array' ? deref(rootCtx.items) : rootCtx;
  formId = 'root>#';
}
const scopes = scopesFor(formId);
for (const p of leafPointers(formCtx)) {
  if (!isCovered(formId, p, scopes)) warnings.push(`not covered by any control: ${p} (cover it or list it as intentionally omitted)`);
}

if (i18n) {
  const prefix = rootCtx.type === 'array' ? '#/items' : '#';
  for (const p of leafPointers(formCtx, prefix)) {
    if (!(`${p}.label` in i18n)) warnings.push(`i18n: missing "${p}.label"`);
  }
  const titles = [];
  const collect = (el) => {
    if (!el || typeof el !== 'object') return;
    if ((el.type === 'Category' || el.type === 'Group') && el.label) titles.push(el.label);
    if (el.type === 'Label' && el.text) titles.push(el.text);
    if (el.type === 'Action') {
      if (el.label) titles.push(el.label);
      const { title, note, fields } = el.params ?? {};
      for (const t of [title, note, ...(fields ?? []).map((f) => f?.label)]) if (typeof t === 'string') titles.push(t);
    }
    (el.elements ?? []).forEach(collect);
    if (el.options?.detail) collect(el.options.detail);
  };
  collect(ui);
  for (const t of titles) if (!(t in i18n)) warnings.push(`i18n: missing raw-text key "${t}"`);
}

for (const e of errors) console.log(`ERROR   ${e}`);
for (const w of warnings) console.log(`WARNING ${w}`);
console.log(`\n${errors.length} error(s), ${warnings.length} warning(s)`);
process.exit(errors.length ? 1 : 0);
