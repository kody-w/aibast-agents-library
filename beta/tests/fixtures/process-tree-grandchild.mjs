import { writeFileSync } from "node:fs";

writeFileSync(process.argv[2], `${process.pid}\n`);
process.on("SIGTERM", () => {});
setInterval(() => {}, 1_000);
