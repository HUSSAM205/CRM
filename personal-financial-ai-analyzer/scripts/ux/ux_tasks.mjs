// Real-browser user-task validation (master prompt section 24; HW1 3.2.6; HW2 E4).
// Usage: node scripts/ux/ux_tasks.mjs http://localhost:8501
// Drives the running Streamlit app like a user (real file-upload widget, clicks, typing), records
// completion, errors and duration per task, saves a screenshot per task, writes results JSON.
// No real participants are involved: this is scripted task validation, not a user study.
import { createRequire } from "node:module";
const { chromium } = createRequire(import.meta.url)("playwright");
import fs from "node:fs";
import path from "node:path";

const BASE = process.argv[2] || "http://localhost:8501";
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
const EXP = JSON.parse(fs.readFileSync(path.join(ROOT, "reports/ux_tasks/expected.json"), "utf8"));
const SHOTS = path.join(ROOT, "reports/screenshots");
fs.mkdirSync(SHOTS, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 2 });
const results = [];
const idle = async () => {
  await page.waitForTimeout(300);
  await page.waitForFunction(() => !document.querySelector('[data-testid="stStatusWidget"]'), null, { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(400);
};
const nav = async (name) => { await page.getByRole("link", { name, exact: true }).click(); await idle(); };
const main = () => page.locator('[data-testid="stMain"]');

async function task(id, name, fn) {
  const t0 = Date.now();
  let ok = false, error = null, detail = null;
  try { detail = await fn(); ok = true; } catch (e) { error = String(e.message || e).split("\n")[0]; }
  const file = `ux_${String(id).padStart(2, "0")}_${name.toLowerCase().replace(/[^a-z0-9]+/g, "_")}.png`;
  await page.screenshot({ path: path.join(SHOTS, file), fullPage: true }).catch(() => {});
  results.push({ id, task: name, completed: ok, seconds: (Date.now() - t0) / 1000, error, detail, screenshot: `reports/screenshots/${file}` });
  console.log(`${ok ? "PASS" : "FAIL"} ${id}. ${name}${error ? " — " + error : ""}`);
}
const upload = async (file) => {
  await page.locator('[data-testid="stFileUploader"] input[type="file"]').setInputFiles(path.join(ROOT, file));
  await idle();
};
const expectText = async (loc, text) => { await loc.getByText(text, { exact: false }).first().waitFor({ timeout: 15000 }); };
const deleteData = async () => { await page.getByRole("button", { name: "Delete my data now" }).click(); await idle(); };

await page.goto(BASE); await idle();

await task(1, "Upload a valid CSV", async () => {
  await nav("Transactions");
  await upload("data/samples/sample_bank_export.csv");
  await page.getByText("All rows in this file are completed").click(); await idle();
  await page.getByRole("button", { name: "Validate and load" }).click(); await idle();
  await expectText(page.locator('[data-testid="stSidebar"]'), "Loaded: upload: sample_bank_export.csv");
  return "bank-style signed CSV mapped and loaded";
});

await task(2, "Reject an invalid timestamp", async () => {
  await deleteData(); await nav("Transactions");
  await upload("tests/fixtures/invalid_rows.csv");
  await page.getByRole("button", { name: "Validate and load" }).click(); await idle();
  await expectText(main(), "Date/time could not be read");
  return "invalid_timestamp row reported with explanation";
});

await task(3, "Reject an invalid amount", async () => {
  await expectText(main(), "Amount is not a number");
  const rejected = await main().locator('[data-testid="stMetric"]', { hasText: "Rejected rows" }).locator('[data-testid="stMetricValue"]').innerText();
  if (rejected.trim() !== String(EXP.invalid_file_rejected_rows)) throw new Error(`rejected=${rejected}`);
  return `rejected rows shown = ${rejected}`;
});

await task(4, "Map missing columns", async () => {
  await deleteData(); await nav("Transactions");
  await upload("tests/fixtures/unmapped_columns.csv");
  await page.getByLabel("Date / time *").click(); await page.keyboard.type("When"); await page.keyboard.press("Enter"); await idle();
  await page.getByLabel("Category", { exact: true }).first().click(); await page.keyboard.type("Kind"); await page.keyboard.press("Enter"); await idle();
  await page.getByText("All rows in this file are completed").click(); await idle();
  await page.getByRole("button", { name: "Validate and load" }).click(); await idle();
  await expectText(page.locator('[data-testid="stSidebar"]'), "Loaded: upload: unmapped_columns.csv");
  const valid = await main().locator('[data-testid="stMetric"]', { hasText: "Valid rows" }).locator('[data-testid="stMetricValue"]').innerText();
  if (valid.trim() !== String(EXP.unmapped_rows)) throw new Error(`valid=${valid}`);
  return "When->date and Kind->category mapped by the user; 3 rows valid";
});

await task(5, "View monthly totals", async () => {
  await deleteData(); await nav("Transactions");
  await page.getByRole("button", { name: "Load demo data" }).click(); await idle();
  await nav("Overview");
  await page.locator('[data-testid="stSidebar"]').getByLabel("Currency", { exact: true }).click(); await page.keyboard.type("USD"); await page.keyboard.press("Enter"); await idle();
  const val = async (label) => main().locator('[data-testid="stMetric"]', { hasText: label }).first().locator('[data-testid="stMetricValue"]').innerText();
  const got = { income: await val("Income (inflows)"), expenses: await val("Expenses"), net: await val("Net cash flow") };
  for (const k of ["income", "expenses", "net"]) if (got[k].trim() !== EXP[k]) throw new Error(`${k}: ${got[k]} != ${EXP[k]}`);
  return got;
});

await task(6, "Filter a category", async () => {
  await nav("Transactions");
  await page.getByLabel("Category", { exact: true }).last().click(); await page.keyboard.type("groceries"); await page.keyboard.press("Enter");
  await page.keyboard.press("Escape"); await idle();   // close the dropdown (it overlays the page)
  await expectText(main(), `${EXP.groceries_rows} transactions.`);
  return `${EXP.groceries_rows} groceries transactions shown`;
});

await task(7, "Change a budget", async () => {
  await nav("Budget");
  await main().getByRole("combobox").first().click(); await page.keyboard.type(EXP.budget_month); await page.keyboard.press("Enter"); await idle();
  await page.waitForTimeout(2000);   // the editor re-renders under a new key after the month changes
  const grid = main().locator('[data-testid="stDataFrame"] canvas').first();   // the grid canvas, not its container
  const box = await grid.boundingBox();
  // double-click the budget cell (2nd column) of the target row: header ~35px, rows ~35px (CSS px)
  await page.mouse.dblclick(box.x + 250, box.y + 35 + 35 * (EXP.budget_row_index + 0.5)); await page.waitForTimeout(800);
  await page.keyboard.press("ControlOrMeta+a"); await page.keyboard.type("0.01"); await page.keyboard.press("Enter"); await idle();
  await expectText(main(), `${EXP.budget_category}: Over budget`);
  return `${EXP.budget_category} budget set to 0.01 -> over-budget alert shown`;
});

await task(8, "View a forecast", async () => {
  await nav("AI predictions");
  await expectText(main(), "Expected spending in");
  return (await main().locator('[data-testid="stMetric"]').first().innerText()).replace(/\n/g, " ");
});

await task(9, "View anomaly candidates", async () => {
  await expectText(main(), "Anomaly review candidate (not confirmed fraud)");
  return "candidate table labelled as review candidates";
});

await task(10, "Ask a supported question", async () => {
  await nav("Financial assistant");
  await page.getByLabel("Ask a question").fill(`How much did I spend in ${EXP.last_month}?`);
  await page.getByRole("button", { name: "Ask" }).click(); await idle();
  await expectText(main(), `Your total spending in ${EXP.last_month} was ${EXP.last_month_spend}.`);
  return `answer matched dashboard value ${EXP.last_month_spend}`;
});

await task(11, "Ask an unsupported question", async () => {
  await page.getByLabel("Ask a question").fill("Which stocks should I buy?");
  await page.getByRole("button", { name: "Ask" }).click(); await idle();
  await expectText(main(), "Sorry, I can't answer that question.");
  return "fixed unsupported reply";
});

await task(12, "Delete uploaded data", async () => {
  await deleteData();
  await expectText(page.locator('[data-testid="stSidebar"]'), "No data loaded");
  await nav("Overview");
  await expectText(main(), "Load data first");
  return "data purged; pages show the empty state";
});

await task(13, "Switch account (isolation)", async () => {
  await nav("Transactions");
  await page.getByRole("button", { name: "Load demo data" }).click(); await idle();
  await nav("Overview");
  const sb = page.locator('[data-testid="stSidebar"]');
  await sb.getByLabel("Account", { exact: true }).click(); await page.keyboard.type(EXP.account2); await page.keyboard.press("Enter"); await idle();
  const val = async (label) => main().locator('[data-testid="stMetric"]', { hasText: label }).first().locator('[data-testid="stMetricValue"]').innerText();
  const got = { expenses: (await val("Expenses")).trim(), income: (await val("Income (inflows)")).trim() };
  if (got.expenses !== EXP.account2_expenses || got.income !== EXP.account2_income)
    throw new Error(`account2 totals ${JSON.stringify(got)} != ${EXP.account2_expenses} / ${EXP.account2_income}`);
  return `switched to ${EXP.account2} (${EXP.account2_currency}); totals equal that account's own data`;
});

await task(14, "Invalid upload keeps existing data", async () => {
  fs.writeFileSync("/tmp/all_invalid.csv", "Date,Amount,Currency\nnot-a-date,abc,XXX\n");
  await nav("Transactions");
  await page.locator('[data-testid="stFileUploader"] input[type="file"]').setInputFiles("/tmp/all_invalid.csv"); await idle();
  await page.getByText("All rows in this file are completed").click(); await idle();
  await page.getByRole("button", { name: "Validate and load" }).click(); await idle();
  await expectText(main(), "No valid rows remained");
  await expectText(page.locator('[data-testid="stSidebar"]'), "Loaded: demo");
  return "fully invalid file rejected with a message; previously loaded demo data still active";
});

// Date-range filter: Streamlit 1.67 renders it as hidden native date inputs that cannot be driven by a
// browser script; it is verified through the real widget state in tests/integration/test_dashboard.py
// (test_transactions_date_filter).

await task(16, "Reload the application", async () => {
  await page.reload(); await idle();
  await expectText(page.locator('[data-testid="stSidebar"]'), "No data loaded");
  return "a reload starts a new session: uploaded data is not persisted (privacy by design)";
});

// fresh screenshots of all six pages with demo data
await nav("Transactions"); await page.getByRole("button", { name: "Load demo data" }).click(); await idle();
for (const [name, file] of [["Overview", "page_1_overview"], ["Transactions", "page_2_transactions"], ["Analytics", "page_3_analytics"],
                            ["AI predictions", "page_4_ai_predictions"], ["Budget", "page_5_budget"], ["Financial assistant", "page_6_assistant"]]) {
  await nav(name); await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(SHOTS, `${file}.png`), fullPage: true });
}

await browser.close();
const summary = { run_at_utc: new Date().toISOString(), base_url: BASE, tasks: results.length,
  completed: results.filter(r => r.completed).length, errors: results.filter(r => !r.completed).length,
  mean_seconds: results.reduce((a, r) => a + r.seconds, 0) / results.length, results };
fs.writeFileSync(path.join(ROOT, "reports/ux_tasks/ux_task_results.json"), JSON.stringify(summary, null, 2));
console.log(`completed ${summary.completed}/${summary.tasks}`);
