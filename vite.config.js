import { resolve } from "node:path";
import { readdirSync } from "node:fs";

// Every page build.py writes next to this file (index, tantra, massages, masseuses, girl-*)
const pages = Object.fromEntries(readdirSync(__dirname).filter((f) => f.endsWith(".html")).map((f) => [f.slice(0, -5), resolve(__dirname, f)]));
export default { build: { rollupOptions: { input: pages } } };
