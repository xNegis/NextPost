// Headless DOM/HTTP integration only: no screenshots or visual assertions (DEC-034).
// Requires the disposable RF-12 Compose project, Node 24 and installed Chrome.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { mkdtemp, rm } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const profile = await mkdtemp(path.join(root, ".env.rf12-browser-"));
const chrome = spawn(
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  [
    "--headless=new",
    "--no-first-run",
    "--no-default-browser-check",
    "--remote-debugging-port=19222",
    `--user-data-dir=${profile}`,
    "about:blank",
  ],
  { windowsHide: true, stdio: "ignore" },
);
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
let socket;
let id = 0;
const pending = new Map();

async function cdp(method, params = {}) {
  const requestId = ++id;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(requestId);
      reject(new Error(`CDP timeout: ${method}`));
    }, 25000);
    pending.set(requestId, {
      resolve: (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      reject,
    });
    socket.send(JSON.stringify({ id: requestId, method, params }));
  });
}

async function run(expression) {
  const result = await cdp("Runtime.evaluate", {
    expression: `(async () => { ${expression} })()`,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails)
    throw new Error(
      result.exceptionDetails.exception?.description ??
        "Browser assertion failed",
    );
  return result.result.value;
}

async function helpers() {
  for (let attempt = 0; attempt < 20; attempt++) {
    try {
      await run(`
    window.check = (condition, message) => { if (!condition) throw Error(message); };
    window.until = async (condition) => {
      for (let i = 0; i < 150; i++) { const value = condition(); if (value) return value; await new Promise(r => setTimeout(r, 100)); }
      throw Error('DOM condition timed out');
    };
    window.button = (text) => [...document.querySelectorAll('button')].find(b => b.textContent.trim() === text && !b.closest('[hidden]') && !b.disabled);
    window.click = async (text) => (await until(() => button(text))).click();
    window.heading = (text) => document.querySelector('h1')?.textContent === text;
    window.fill = (selector, value) => {
      const input = document.querySelector(selector);
      Object.getOwnPropertyDescriptor(input instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype, 'value').set.call(input, value);
      input.dispatchEvent(new Event('input', { bubbles: true }));
    };
    await until(() => document.querySelector('h1'));
      `);
      return;
    } catch (error) {
      if (
        !/Execution context was destroyed|Cannot find context/.test(
          error.message,
        ) ||
        attempt === 19
      )
        throw error;
      await delay(200);
    }
  }
}

try {
  let target;
  for (let attempt = 0; attempt < 80; attempt++) {
    try {
      target = await (
        await fetch("http://127.0.0.1:19222/json/new?http://localhost:14173", {
          method: "PUT",
        })
      ).json();
      break;
    } catch {
      await delay(100);
    }
  }
  assert.ok(target?.webSocketDebuggerUrl, "Isolated Chrome did not start");
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await once(socket, "open");
  socket.addEventListener("message", ({ data }) => {
    const message = JSON.parse(data);
    const request = pending.get(message.id);
    if (!request) return;
    pending.delete(message.id);
    if (message.error) request.reject(new Error(message.error.message));
    else request.resolve(message.result);
  });
  await cdp("Runtime.enable");
  await cdp("Page.enable");
  await helpers();
  const suffix = crypto.randomUUID().replaceAll("-", "").slice(0, 8);
  const email = `rf12browser${suffix}@example.com`;
  const password = "rf12-disposable-test-password";
  await run(
    `const response = await fetch('http://localhost:18000/api/accounts', { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify(${JSON.stringify({ email, alias: `Browser${suffix}`, password })}) }); check(response.status === 201, 'Register isolated browser account');`,
  );
  await cdp("Page.reload");
  await delay(400);
  await helpers();
  await run(
    "await until(() => button('Home')); check(document.querySelector('[aria-current=page]').textContent.trim() === 'Home', 'Home is the restored default');",
  );
  for (const audience of ["public", "private"]) {
    await run(`
      await click('Create'); await until(() => document.querySelector('input[type=file]:not(:disabled)'));
      const files = new DataTransfer();
      for (const color of ['red', 'blue']) {
        const canvas = document.createElement('canvas'); canvas.width = 64; canvas.height = 80;
        const ctx = canvas.getContext('2d'); ctx.fillStyle = color; ctx.fillRect(0, 0, 64, 80);
        const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg'));
        files.items.add(new File([blob], color + '.jpg', {type:'image/jpeg'}));
      }
      const input = document.querySelector('input[type=file]'); input.files = files.files; input.dispatchEvent(new Event('change', { bubbles:true }));
      await click('Continue');
      await until(() => document.querySelector('#consultation-question')?.closest('[hidden]') === null);
      fill('#consultation-question', 'Browser ${audience} choice?');
      document.querySelector('input[type=radio][value=${audience}]').click();
      await click('Continue'); await click('Publish consultation');
      await until(() => heading('Published')); await click('View in My consultations');
      await until(() => heading('Your consultation') && document.querySelectorAll('.owner-consultation img').length === 2);
      check(!document.body.textContent.includes('Your consultation is now live.'), 'Returning detail is neutral');
      check([...document.querySelectorAll('.owner-consultation img')].every(img => img.src.startsWith('blob:')), 'Protected photos loaded');
      await click('Back to My consultations'); await until(() => heading('My consultations'));
      await until(() => button('View consultation'));
    `);
  }
  await cdp("Page.reload");
  await delay(400);
  await helpers();
  await run(
    `await click('My consultations'); await until(() => [...document.querySelectorAll('button')].filter(b => b.textContent.trim() === 'View consultation').length === 2); await click('View consultation'); await until(() => document.querySelectorAll('.owner-consultation img').length === 2); await click('Profile'); await click('Sign out'); await until(() => document.querySelector('#signin-email')); fill('#signin-email', ${JSON.stringify(email)}); fill('#signin-password', ${JSON.stringify(password)}); await click('Sign in'); await until(() => button('My consultations')); check(document.querySelector('[aria-current=page]').textContent.trim() === 'Home', 'Home after sign in'); await click('My consultations'); await until(() => [...document.querySelectorAll('button')].filter(b => b.textContent.trim() === 'View consultation').length === 2); await click('Finalized'); await until(() => document.body.textContent.includes('You have no finalized consultations.'));`,
  );
  console.log(
    "PASS: real built Chrome client publishes Public/Private through composer; publication-to-owner-detail handoff; Back/list recovery; protected photos; reload; sign out/in; Home default; finalized empty state. No visual checks.",
  );
} finally {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ id: ++id, method: "Browser.close" }));
    socket.close();
  }
  await Promise.race([once(chrome, "exit").catch(() => {}), delay(3000)]);
  if (chrome.exitCode === null) chrome.kill();
  // Only the unique directory created by this script inside the repository is removed.
  if (
    path.dirname(path.resolve(profile)) === root &&
    path.basename(profile).startsWith(".env.rf12-browser-")
  ) {
    await rm(profile, {
      recursive: true,
      force: true,
      maxRetries: 5,
      retryDelay: 200,
    });
  }
}
