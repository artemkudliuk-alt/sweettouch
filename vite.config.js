import { resolve } from "node:path";

export default {
  build: { rollupOptions: { input: { main: resolve(__dirname, "index.html"), tantra: resolve(__dirname, "tantra.html") } } },
};
