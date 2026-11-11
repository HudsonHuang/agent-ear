#!/usr/bin/env node
/**
 * One-command npm bootstrap:
 *
 *   npx -y agent-ear@latest setup
 *
 * Installs the CLI (and ffmpeg/uv on Windows) by running the repo's installer,
 * then hands off to the real Python `agent-ear setup` for Qwen key + skills.
 */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const args = process.argv.slice(2);
const command = args[0] || "setup";
const rest = args.slice(1);

function help() {
  console.log(`agent-ear npm bootstrap

Usage:
  npx -y agent-ear@latest setup [setup args]

Examples:
  npx -y agent-ear@latest setup
  npx -y agent-ear@latest setup --target dsh
  npx -y agent-ear@latest setup --skip-key

It installs ffmpeg/uv/agent-ear when needed, then runs \`agent-ear setup\`.
`);
}

if (command === "--help" || command === "-h" || command === "help") {
  help();
  process.exit(0);
}
if (command !== "setup" && command !== "install") {
  console.error(`unknown command: ${command}`);
  help();
  process.exit(2);
}

function run(cmd, argv, opts = {}) {
  return new Promise((resolve) => {
    const p = spawn(cmd, argv, { stdio: "inherit", ...opts });
    p.on("error", (err) => {
      console.error(`${cmd}: ${err.message}`);
      resolve(127);
    });
    p.on("exit", (code, signal) => resolve(code ?? (signal ? 128 : 1)));
  });
}

async function installer() {
  if (process.platform === "win32") {
    const script = join(ROOT, "install.ps1");
    if (!existsSync(script)) throw new Error(`missing installer: ${script}`);
    return run("powershell.exe", [
      "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, "-SkipSetup",
    ]);
  }
  const script = join(ROOT, "install.sh");
  if (!existsSync(script)) throw new Error(`missing installer: ${script}`);
  return run("bash", [script], {
    env: { ...process.env, AGENT_EAR_SKIP_SETUP: "1" },
  });
}

function findCli() {
  if (process.env.AGENT_EAR_BIN && existsSync(process.env.AGENT_EAR_BIN)) {
    return process.env.AGENT_EAR_BIN;
  }
  const win = process.platform === "win32";
  const candidates = win
    ? [join(homedir(), ".local", "bin", "agent-ear.exe")]
    : [join(homedir(), ".local", "bin", "agent-ear")];
  return candidates.find((p) => existsSync(p)) || null;
}

const rc = await installer();
if (rc !== 0) {
  console.error(`installer failed (exit ${rc})`);
  process.exit(rc === 0 ? 1 : rc);
}

const cli = findCli();
if (!cli) {
  console.error("agent-ear CLI was not found after install.");
  console.error("Open a new terminal and run: agent-ear setup");
  process.exit(127);
}

console.log(`\n==> ${cli} setup ${rest.join(" ")}`.trim());
const setupRc = await run(cli, ["setup", ...rest]);
process.exit(setupRc === 0 ? 0 : setupRc);
