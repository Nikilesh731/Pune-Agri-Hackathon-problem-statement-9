const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();
const OUTPUT_DIR = path.join(ROOT, "docs");
const OUTPUT_FILE = path.join(OUTPUT_DIR, "PROJECT_BRAIN.md");

const INCLUDE_FOLDERS = [
  "backend/src",
  "frontend/src",
  "ai-services/app",
  "scripts",
  "docs"
];

const EXCLUDE_DIRS = new Set([
  "node_modules",
  ".git",
  "dist",
  "build",
  ".next",
  ".turbo",
  ".vercel",
  "coverage",
  ".idea",
  ".vscode",
  "__pycache__",
  ".pytest_cache",
  ".DS_Store",
  "venv",
  ".venv",
  "generated",
  "migrations"
]);

const FILE_EXTENSIONS = new Set([
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".py",
  ".json",
  ".md"
]);

function shouldSkipDir(name) {
  return EXCLUDE_DIRS.has(name);
}

function shouldIncludeFile(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  return FILE_EXTENSIONS.has(ext);
}

function safeRead(filePath) {
  try {
    return fs.readFileSync(filePath, "utf8");
  } catch {
    return "";
  }
}

function getTopComment(content, ext) {
  const trimmed = content.trimStart();

  if (ext === ".py") {
    const tripleDouble = trimmed.match(/^"""([\s\S]*?)"""/);
    if (tripleDouble) return cleanComment(tripleDouble[1]);

    const tripleSingle = trimmed.match(/^'''([\s\S]*?)'''/);
    if (tripleSingle) return cleanComment(tripleSingle[1]);

    const hashLines = [];
    for (const line of trimmed.split("\n").slice(0, 12)) {
      const m = line.match(/^\s*#\s?(.*)$/);
      if (!m) break;
      hashLines.push(m[1]);
    }
    if (hashLines.length) return cleanComment(hashLines.join("\n"));
    return "";
  }

  const block = trimmed.match(/^\/\*\*?([\s\S]*?)\*\//);
  if (block) return cleanComment(block[1]);

  const slashLines = [];
  for (const line of trimmed.split("\n").slice(0, 12)) {
    const m = line.match(/^\s*\/\/\s?(.*)$/);
    if (!m) break;
    slashLines.push(m[1]);
  }
  if (slashLines.length) return cleanComment(slashLines.join("\n"));

  return "";
}

function cleanComment(text) {
  return text
    .split("\n")
    .map((line) => line.replace(/^\s*\*\s?/, "").trim())
    .filter(Boolean)
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

function getExportsSummary(content, ext) {
  if (![".ts", ".tsx", ".js", ".jsx", ".py"].includes(ext)) return "";

  const lines = content.split("\n").slice(0, 80).join("\n");
  const matches = [];

  const patterns = [
    /export function (\w+)/g,
    /export const (\w+)/g,
    /export class (\w+)/g,
    /class (\w+)/g,
    /def (\w+)\(/g
  ];

  for (const pattern of patterns) {
    let m;
    while ((m = pattern.exec(lines)) !== null) {
      matches.push(m[1]);
    }
  }

  const unique = [...new Set(matches)].slice(0, 6);
  return unique.length ? `Exports/Defines: ${unique.join(", ")}` : "";
}

function walk(dir, results = []) {
  if (!fs.existsSync(dir)) return results;

  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    if (shouldSkipDir(entry.name)) continue;

    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      walk(fullPath, results);
      continue;
    }

    if (!shouldIncludeFile(fullPath)) continue;

    const content = safeRead(fullPath);
    const ext = path.extname(fullPath).toLowerCase();
    const rel = path.relative(ROOT, fullPath).replace(/\\/g, "/");
    const comment = getTopComment(content, ext);
    const exportsSummary = getExportsSummary(content, ext);

    results.push({
      path: rel,
      summary: comment || "No top-level summary comment found.",
      exportsSummary
    });
  }

  return results;
}

function groupByFolder(files) {
  const grouped = new Map();

  for (const file of files) {
    const folder = path.dirname(file.path);
    if (!grouped.has(folder)) grouped.set(folder, []);
    grouped.get(folder).push(file);
  }

  return [...grouped.entries()].sort((a, b) => a[0].localeCompare(b[0]));
}

function generateMarkdown(files) {
  const now = new Date().toISOString();
  const grouped = groupByFolder(files);

  const lines = [];
  lines.push("# PROJECT_BRAIN");
  lines.push("");
  lines.push(`Generated: ${now}`);
  lines.push("");
  lines.push("## Purpose");
  lines.push("");
  lines.push("This file is an auto-generated project summary for quickly bootstrapping a new AI/chat session with the current codebase context.");
  lines.push("");

  for (const [folder, items] of grouped) {
    lines.push(`## ${folder}`);
    lines.push("");

    for (const item of items.sort((a, b) => a.path.localeCompare(b.path))) {
      lines.push(`### ${path.basename(item.path)}`);
      lines.push("");
      lines.push(`- Path: \`${item.path}\``);
      lines.push(`- Summary: ${item.summary}`);
      if (item.exportsSummary) {
        lines.push(`- ${item.exportsSummary}`);
      }
      lines.push("");
    }
  }

  return lines.join("\n");
}

function main() {
  const files = [];

  for (const folder of INCLUDE_FOLDERS) {
    walk(path.join(ROOT, folder), files);
  }

  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const markdown = generateMarkdown(files);
  fs.writeFileSync(OUTPUT_FILE, markdown, "utf8");

  console.log(`Generated: ${path.relative(ROOT, OUTPUT_FILE)}`);
  console.log(`Files summarized: ${files.length}`);
}

main();