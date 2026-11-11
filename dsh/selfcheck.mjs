/**
 * Self-check for the DSH skill provider.
 *
 * Runs without a DSH host: it imports the plugin, drives `apply()` with a fake
 * `ctx.skills`, and asserts the provider contract the catalog relies on.
 * Also guards the two things that silently broke in earlier releases:
 * a description that drifts from SKILL.md, and a missing skill body.
 */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import { apply, inject, name, parseDescription, provider } from "./index.js";

const SKILL_MD = fileURLToPath(new URL("../skills/agent-ear/SKILL.md", import.meta.url));

// 1. Cordis plugin surface
assert.equal(name, "agent-ear");
assert.deepEqual(inject, ["skills"]);

// 2. apply() registers exactly one provider factory
let factory = null;
apply({ skills: { registerProvider: (f) => { factory = f; } } });
assert.equal(typeof factory, "function", "apply() must call ctx.skills.registerProvider");
const registered = factory();
assert.equal(registered.name, "agent-ear");

// 3. list()/get() agree, and both carry a real description
const [listed] = await provider.list();
assert.equal(listed.name, "agent-ear");
assert.equal(listed.source, "bundled");
assert.ok(listed.description.length > 40, "description looks truncated");
assert.ok(listed.resourceBase.path.endsWith("skills/agent-ear/"));

const got = await provider.get(listed);
assert.equal(got.name, listed.name);
assert.equal(got.description, listed.description);
assert.ok(got.content.startsWith("---"), "skill body must keep its frontmatter");
assert.ok(got.content.includes("# agent-ear"), "skill body looks empty");

// 4. The description is parsed from SKILL.md, never hardcoded
const markdown = await readFile(SKILL_MD, "utf8");
assert.equal(got.description, parseDescription(markdown));
assert.equal(listed.description, parseDescription(markdown));

// 5. Frontmatter parsing handles the shapes skill authors actually write
assert.equal(parseDescription("---\ndescription: inline value\n---\n"), "inline value");
assert.equal(
  parseDescription("---\ndescription: >-\n  folded\n  lines\n---\nbody"),
  "folded lines",
);
assert.equal(parseDescription("no frontmatter here"), "");

console.log("agent-ear dsh selfcheck: ok");
