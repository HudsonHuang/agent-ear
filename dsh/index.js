/**
 * DeepSeek Harness skill provider for agent-ear.
 *
 * The skill body is `skills/agent-ear/SKILL.md`, which stays the single source of
 * truth for the description: it is parsed out of the frontmatter at load time so
 * the DSH catalog can never drift from the skill file.
 *
 * @module agent-ear/dsh
 */
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { BUNDLED_SKILL_RANK } from "@deepseek-ai/dsh-skill";

const PROVIDER_NAME = "agent-ear";
const SKILL_NAME = "agent-ear";
const SKILL_DIR_URL = new URL("../skills/agent-ear/", import.meta.url);
const SKILL_BODY_URL = new URL("../skills/agent-ear/SKILL.md", import.meta.url);
const RESOURCE_BASE = {
  kind: "directory",
  path: fileURLToPath(SKILL_DIR_URL),
};

const FALLBACK_DESCRIPTION =
  "Give text-only agents an ear for offline audio/video: turn speech, sound " +
  "events, and music into one timestamped audio-score.json plus a hierarchical " +
  "hearing.md.";

/**
 * Read `description:` from a SKILL.md YAML frontmatter block.
 *
 * Only supports what skill frontmatter actually uses: either an inline value or a
 * folded/literal block (`>-`, `>`, `|`, `|-`) followed by indented lines.
 *
 * @param {string} markdown Skill file contents.
 * @returns {string} Description, or an empty string when absent.
 */
export function parseDescription(markdown) {
  const match = /^---\r?\n([\s\S]*?)\r?\n---\r?\n/.exec(markdown);
  if (!match) return "";
  const lines = match[1].split(/\r?\n/);
  const start = lines.findIndex((line) => /^description:/.test(line));
  if (start < 0) return "";
  const inline = lines[start].slice("description:".length).trim();
  if (inline && inline !== ">" && inline !== ">-" && inline !== "|" && inline !== "|-") {
    return inline;
  }
  const body = [];
  for (const line of lines.slice(start + 1)) {
    if (line.trim() === "") {
      if (body.length) body.push("");
      continue;
    }
    if (!/^\s/.test(line)) break;
    body.push(line.trim());
  }
  return body.join(" ").replace(/\s+/g, " ").trim();
}

async function describe() {
  const markdown = await readFile(SKILL_BODY_URL, "utf8");
  return parseDescription(markdown) || FALLBACK_DESCRIPTION;
}

const candidate = async () => ({
  name: SKILL_NAME,
  description: await describe(),
  invocation: { modelInvocable: true, userInvocable: true },
  provider: PROVIDER_NAME,
  source: "bundled",
  resourceBase: RESOURCE_BASE,
  rank: BUNDLED_SKILL_RANK,
  locator: SKILL_BODY_URL,
});

const provider = {
  name: PROVIDER_NAME,
  list: async () => [await candidate()],
  async get() {
    const base = await candidate();
    return {
      name: base.name,
      description: base.description,
      invocation: base.invocation,
      provider: base.provider,
      source: base.source,
      resourceBase: base.resourceBase,
      content: await readFile(SKILL_BODY_URL, "utf8"),
    };
  },
};

/** Cordis plugin name. */
export const name = "agent-ear";

/** Service required by the skill provider. */
export const inject = ["skills"];

/**
 * Register the agent-ear skill provider on `ctx.skills`.
 * @param {{ skills: { registerProvider: (factory: () => unknown) => void } }} ctx
 */
export function apply(ctx) {
  ctx.skills.registerProvider(() => provider);
}

export { provider };
