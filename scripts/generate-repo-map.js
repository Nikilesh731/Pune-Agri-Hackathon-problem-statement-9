const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();

const INCLUDE_FOLDERS = ["frontend", "backend", "ai-services", "shared", "docs"];

const EXCLUDE = [
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
  "venv"
];

function isExcluded(name) {
  return EXCLUDE.includes(name);
}

function getValidItems(dir) {
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter(item => !isExcluded(item.name))
    .sort((a, b) => {
      // folders first, then files
      if (a.isDirectory() && !b.isDirectory()) return -1;
      if (!a.isDirectory() && b.isDirectory()) return 1;
      return a.name.localeCompare(b.name);
    });
}

function buildTree(dir, prefix = "") {
  const items = getValidItems(dir);

  let lines = [];

  items.forEach((item, index) => {
    const isLast = index === items.length - 1;
    const connector = isLast ? "└── " : "├── ";

    const fullPath = path.join(dir, item.name);
    lines.push(prefix + connector + item.name);

    if (item.isDirectory()) {
      const newPrefix = prefix + (isLast ? "    " : "│   ");
      lines = lines.concat(buildTree(fullPath, newPrefix));
    }
  });

  return lines;
}

function generate() {
  let output = [];

  output.push(`# Repo Map`);
  output.push(``);
  output.push(`> Generated automatically on ${new Date().toISOString()}`);
  output.push(`> Do not edit manually - run \`npm run repo:map\``);
  output.push(``);

  output.push(`## Project Structure`);
  output.push(``);
  output.push("```text");

  INCLUDE_FOLDERS.forEach(folder => {
    const fullPath = path.join(ROOT, folder);

    if (fs.existsSync(fullPath)) {
      output.push(`${folder}/`);
      const tree = buildTree(fullPath, "  ");
      output = output.concat(tree);
    }
  });

  output.push("```");

  const docsDir = path.join(ROOT, "docs");
  const outputPath = path.join(docsDir, "repo-map.md");

  // ensure docs folder exists
  fs.mkdirSync(docsDir, { recursive: true });

  fs.writeFileSync(outputPath, output.join("\n"));

  console.log("✅ docs/repo-map.md generated successfully");
}

// run
generate();