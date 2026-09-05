import { writeFileSync } from "node:fs";

writeFileSync(process.argv[2], `${process.pid}\n`);
setInterval(() => {}, 1_000);
