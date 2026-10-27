// Prueba de interfaz de la v1.4.0 en Chromium (Playwright): versión y modelo por defecto, los tres modelos en el
// selector con su nota, programación y carga con cada modelo, Cp calculada tras la carga, exportación del CSV con
// el código y los parámetros del modelo, y ningún error de JavaScript.
// Uso: node prueba_interfaz_v140.cjs <simulador_tci_dexmedetomidina.html> <carpeta de salida>
const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");

const [HTML, OUT] = process.argv.slice(2);
fs.mkdirSync(OUT, { recursive: true });
const results = [];
const test = (id, desc, pass, detail = "") => { results.push({ id, desc, pass: !!pass, detail }); console.log(`${pass ? "✔" : "✘"} ${id} ${desc}${detail ? " · " + detail : ""}`); };

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ acceptDownloads: true, viewport: { width: 1280, height: 900 } });
  const errors = [];
  page.on("pageerror", e => errors.push(String(e)));
  page.on("console", m => m.type() === "error" && errors.push(m.text()));
  await page.goto("file://" + path.resolve(HTML));
  await page.waitForSelector("#model");

  const body = await page.innerText("body");
  test("UI-V1", "La pantalla muestra la versión 1.4.0", /1\.4\.0/.test(body));
  const opts = await page.$$eval("#model option", os => os.map(o => ({ value: o.value, text: o.textContent })));
  const def = await page.$eval("#model", s => s.value);
  test("UI-V2", "Tres modelos en el selector; por defecto, el corregido", opts.length === 3 && def === "corregido",
    opts.map(o => o.text).join(" | "));

  const display = async label => page.evaluate(l => {
    const el = [...document.querySelectorAll(".tci-display")].find(d => d.textContent.includes(l));
    return el ? el.textContent : null;
  }, label);
  const expectNote = { corregido: /V1 2\.7 L\/kg y V2 0\.72 L\/kg/, anestesiado: /solo amplía el aclaramiento/, publicado: /Modelo original de Levionnois/ };
  const loads = {};
  for (const model of ["corregido", "anestesiado", "publicado"]) {
    await page.selectOption("#model", model);
    await page.fill("#weight", "15");
    await page.fill("#targetCp", "1.0");
    await page.fill("#duration", "30");
    const note = await page.innerText(".tci-note--field");
    test(`UI-${model}-1`, `Nota del modelo «${model}» bajo el selector`, expectNote[model].test(note), note.slice(0, 90));
    await page.click("text=Programar infusión");
    await page.waitForSelector("text=Protocolo programado");
    const prot = await page.innerText("body");
    const m = prot.match(/Carga \(10 min\)\s*[\s\S]*?([\d.,]+) µg\/kg/);
    loads[model] = m ? Number(m[1].replace(",", ".")) : NaN;
    const label = opts.find(o => o.value === model).text.replace(" · por defecto", "");
    test(`UI-${model}-2`, "El protocolo programado muestra el modelo y la carga", /protocolo programado/i.test(prot) && prot.includes(label)
      && Number.isFinite(loads[model]), `${label} · carga ${loads[model]} µg/kg`);
    const ack = await page.$('label:has-text("Confirmo") input[type="checkbox"], .tci-ack input[type="checkbox"]');
    if (ack && !(await ack.isChecked())) await ack.check();
    await page.selectOption("label:has-text('Velocidad') select", "60");
    await page.click("button:has-text('Iniciar')");
    await page.waitForTimeout(13000);                         // 13 s × 60 = 13 min simulados: la carga (10 min) ha terminado
    const cpText = await display("Cp calculada");
    const cp = cpText ? Number((cpText.match(/([\d.]+)\s*ng/) || [])[1]) : NaN;
    test(`UI-${model}-3`, "Tras la carga la Cp calculada está en el objetivo (1,00 ± 0,05 ng/mL)", Math.abs(cp - 1) <= 0.05, `Cp ${cp}`);
    const [download] = await Promise.all([page.waitForEvent("download"), page.click("text=Exportar CSV")]);
    const file = path.join(OUT, `ui_${model}.csv`);
    await download.saveAs(file);
    const csv = fs.readFileSync(file, "utf8");
    const code = (csv.match(/"Código del modelo";"([^"]+)"/) || [])[1];
    test(`UI-${model}-4`, "El CSV exportado lleva la versión y el código del modelo", csv.includes('"1.4.0"') && code === model, `código ${code}`);
    await page.click("button:has-text('Pausar')").catch(() => {});
    await page.reload();
    await page.waitForSelector("#model");
  }
  test("UI-V3", "Con 1 ng/mL la carga del corregido es mayor que la del ampliado (volumen central mayor)",
    loads.corregido > 1.8 * loads.anestesiado, `corregido ${loads.corregido} · ampliado ${loads.anestesiado} · publicado ${loads.publicado} µg/kg`);
  await page.screenshot({ path: path.join(OUT, "pantalla_v140.png"), fullPage: false });
  test("UI-V4", "Ningún error de JavaScript en la página", errors.length === 0, errors.slice(0, 3).join(" | "));
  await browser.close();
  fs.writeFileSync(path.join(OUT, "prueba_interfaz_v140.json"), JSON.stringify({ results, errors }, null, 1));
  console.log(`${results.length} pruebas · ${results.filter(r => !r.pass).length} fallos`);
  process.exit(results.every(r => r.pass) ? 0 : 1);
})();
