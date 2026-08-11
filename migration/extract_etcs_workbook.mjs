import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const [input, output] = process.argv.slice(2);
if (!input || !output) throw new Error("Usage: node extract_etcs_workbook.mjs input.xlsx output.json");
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(input));
const sheets = {};
for (const sheet of workbook.worksheets.items) {
  const used = sheet.getUsedRange(true);
  sheets[sheet.name] = { address: used.address, values: used.values, formulas: used.formulas };
}
await fs.writeFile(output, JSON.stringify({ source: input, sheets }, null, 2), "utf8");
