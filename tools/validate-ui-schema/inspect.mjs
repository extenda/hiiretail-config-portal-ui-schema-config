#!/usr/bin/env node
// Compact view of a JSON Schema so an agent does not have to read the whole file.
// Usage: node tools/validate-ui-schema/inspect.mjs <schema.json>            -> features + outline
//        node tools/validate-ui-schema/inspect.mjs <schema.json> <pointer>  -> that subtree, $refs resolved (depth 3)
import { readFileSync } from 'node:fs';

const [file, pointer] = process.argv.slice(2);
if (!file) {
  console.error('Usage: inspect.mjs <schema.json> [#/properties/a/properties/b]');
  process.exit(2);
}
const root = JSON.parse(readFileSync(file, 'utf8'));
const get = (ref) => ref.replace(/^#\/?/, '').split('/').filter(Boolean).reduce((n, k) => (n ? n[k] : undefined), root);
const deref = (n) => {
  const seen = new Set();
  while (n && n.$ref && !seen.has(n.$ref)) { seen.add(n.$ref); n = get(n.$ref) ?? n; }
  return n;
};

if (pointer) {
  const show = (n, d) => {
    n = deref(n);
    if (!n || typeof n !== 'object' || d > 3) return n && n.$ref ? { $ref: n.$ref } : n;
    if (Array.isArray(n)) return n.map((x) => show(x, d + 1));
    return Object.fromEntries(Object.entries(n).map(([k, v]) => [k, show(v, k === 'properties' || k === 'items' ? d + 1 : d)]));
  };
  const target = pointer === '#' ? root : pointer.replace(/^#\//, '').split('/').reduce((n, k) => (n ? deref(n)[k] ?? deref(n).properties?.[k] : undefined), root);
  console.log(JSON.stringify(show(target, 0), null, 2));
  process.exit(0);
}

const found = {};
const mark = (k, where) => ((found[k] ??= []).length < 5 && found[k].push(where));
const visit = (n, path, seen = new Set()) => {
  if (!n || typeof n !== 'object') return;
  if (Array.isArray(n)) return n.forEach((x, i) => visit(x, `${path}/${i}`, seen));
  if (n.$ref) { if (seen.has(n.$ref)) return; seen.add(n.$ref); mark('$ref', path); return visit(get(n.$ref), path, seen); }
  for (const k of ['if', 'then', 'else', 'dependentRequired', 'oneOf', 'anyOf', 'allOf', 'enum', 'const', 'contentEncoding', 'contentMediaType']) if (k in n) mark(k, path);
  if (n.format) mark(`format:${n.format}`, path);
  if (n.type === 'array') mark('array', path);
  if (n.maxLength > 200) mark('longText', path);
  for (const k of Object.keys(n)) if (k.startsWith('x-')) mark(k, path);
  if (/\b(api|endpoint|url|lookup|fetch(ed)? from|list of .* from|references? .* kind)\b/i.test(n.description ?? '')) mark('possibleEnumSource(check description)', path);
  for (const [k, v] of Object.entries(n)) visit(v, `${path}/${k}`, seen);
};
visit(root, '#');

console.log(`root type: ${root.type ?? 'object'}   title: ${root.title ?? '-'}   bytes: ${readFileSync(file).length}`);
console.log('\nFEATURES (read the matching reference only if listed):');
for (const [k, w] of Object.entries(found)) console.log(`  ${k}: ${w.join(', ')}`);
const base = deref(root.type === 'array' ? root.items : root);
console.log(`\nOUTLINE of ${root.type === 'array' ? 'items' : 'root'} (property: type, leaf count):`);
const leaves = (n, d = 0) => { n = deref(n); if (!n || d > 6) return 1; const ps = Object.values(n.properties ?? {}); return ps.length ? ps.reduce((a, p) => a + leaves(p, d + 1), 0) : 1; };
for (const [k, v] of Object.entries(base?.properties ?? {})) { const n = deref(v); console.log(`  ${k}: ${n?.type ?? (n?.oneOf ? 'oneOf' : n?.anyOf ? 'anyOf' : '?')}, ${leaves(n)} leaf(s)${base.required?.includes(k) ? ', required' : ''}`); }
console.log('\nNext: inspect one top-level property at a time with a pointer argument.');
