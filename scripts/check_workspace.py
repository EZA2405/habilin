"""Optional browser check: NODE_PATH must resolve Playwright; uses installed Chrome."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from habilin.server import make_server


BROWSER_CHECK = r"""
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
(async () => {
  const input = require('node:readline').createInterface({input: process.stdin})[Symbol.asyncIterator]();
  const {url, tokens, screenshots} = JSON.parse((await input.next()).value);
  const browser = await chromium.launch({channel: 'chrome', headless: true});
  try {
    const page = await browser.newPage({viewport: {width: 1600, height: 1100}, reducedMotion: 'reduce'});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(url);
    async function signIn(role) {
      if (await page.locator('#logout').isVisible()) await page.locator('#logout').click();
      await page.locator('#token').fill(tokens[role]);
      await page.locator('#login-form button').click();
      await page.waitForFunction(role => document.body.dataset.role === role, role);
    }
    async function view(expected) {
      assert.equal(await page.locator('body').getAttribute('data-view'), expected);
    }
    async function stage(expected) {
      await page.waitForFunction(expected => document.querySelector('#execution-stage').textContent === expected, expected);
      await page.waitForFunction(() => !document.querySelector('#next-action').disabled);
    }
    async function fits() {
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Horizontal overflow');
    }
    async function mobileScreenshot(role, preference, filename) {
      const mobile = await browser.newPage({viewport: {width: 390, height: 844}, reducedMotion: 'reduce'});
      mobile.on('pageerror', error => errors.push(error.message));
      await mobile.goto(url);
      await mobile.locator('#token').fill(tokens[role]);
      await mobile.locator('#login-form button').click();
      await mobile.waitForFunction(role => document.body.dataset.role === role, role);
      await mobile.locator('#workspace-view').selectOption(preference);
      assert(await mobile.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Mobile horizontal overflow');
      await mobile.screenshot({path: screenshots + '/' + filename, fullPage: true});
      await mobile.close();
    }
    await signIn('operator');
    await view('guided');
    assert.equal(await page.locator('#calculation-details').getAttribute('open'), null);
    await page.locator('#calculation-details summary').click();
    assert(await page.locator('#gross').isVisible());
    await page.locator('#workspace-view').selectOption('professional');
    await view('professional');
    assert(await page.locator('#execution').isVisible());
    await stage('missing_record');
    await page.reload();
    await signIn('operator');
    await view('professional');
    assert.equal(await page.locator('#execution-stage').textContent(), 'missing_record');
    await page.locator('#workspace-view').selectOption('auto');
    await view('guided');
    await page.locator('#next-action').click();
    await stage('await_professional');
    assert.equal(await page.locator('#approval').isVisible(), false);
    await fits();
    await page.screenshot({path: screenshots + '/guided-desktop.png', fullPage: true});
    await mobileScreenshot('operator', 'guided', 'guided-mobile.png');
    await signIn('professional');
    await view('professional');
    assert(await page.locator('#activity-details').getAttribute('open') !== null);
    assert(await page.locator('#approval').isVisible());
    await page.locator('#next-action').click();
    assert(await page.locator('#confirm').evaluate(el => el === document.activeElement));
    await fits();
    await page.screenshot({path: screenshots + '/professional-desktop.png', fullPage: true});
    await page.locator('#workspace-view').selectOption('guided');
    assert(await page.locator('#approval').isVisible());
    await page.locator('#confirm').check();
    await page.locator('#approve-button').click();
    await stage('await_owner');
    await page.locator('#workspace-view').selectOption('auto');
    await signIn('owner');
    await view('guided');
    await page.locator('#workspace-view').selectOption('professional');
    assert(await page.locator('#owner-code').isVisible());
    await page.locator('#confirm').check();
    console.log('OWNER_CODE_REQUIRED');
    const code = (await input.next()).value;
    await page.locator('#owner-code').fill(code);
    await page.locator('#approve-button').click();
    await stage('ready_to_submit');
    await page.locator('#next-action').click();
    await stage('filing_unknown');
    assert((await page.locator('#filing-key').textContent()).startsWith('filing-'));
    await page.locator('#next-action').click();
    await stage('payment_pending');
    await page.locator('#next-action').click();
    await stage('completed');
    assert.equal(await page.locator('#payment-receipt').textContent(), 'SIM-PAY-0001');
    assert.equal(await page.locator('#office-mailbox').textContent(), 'rdo39_collection@bir.gov.ph');
    assert.equal(await page.locator('#outbox-status').textContent(), 'Draft ready · not sent');
    assert.equal(await page.locator('#m-penalty').textContent(), '₱55,500 avoided');
    await page.screenshot({path: screenshots + "/completed-routing-impact.png", fullPage: true});
    await mobileScreenshot('owner', 'professional', 'professional-mobile.png');
    await page.locator('#lock').click();
    await page.locator('#locked-banner').waitFor({state: 'visible'});
    assert.equal(await page.locator('#next-action').getAttribute('data-action'), 'status');
    await page.locator('#close-case').click();
    await page.locator('#close-case').click();
    await stage('closed');
    assert.equal(await page.locator('#case-name').textContent(), 'Closed case EST-001');
    assert.equal(await page.locator('#record-description').textContent(), 'Deleted at case closure');
    assert.equal(await page.locator('#m-deleted').textContent(), 'Yes');
    assert.equal(await page.locator('#m-mismatch').textContent(), '1');
    assert.deepEqual(errors, []);
    console.log('PASS: role defaults, preference persistence, guided details, unchanged approvals, complete filing/payment, lock, case closure, desktop/mobile layouts; no browser errors.');
  } finally { await browser.close(); process.stdin.destroy(); }
})().catch(error => {console.error(error); process.exitCode = 1;});
"""


def main():
    screenshots = Path(__file__).resolve().parents[1] / ".build/interface-review"
    screenshots.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="habilin-workspace-check-") as directory:
        server = make_server(directory, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            process = subprocess.Popen(
                ["node", "-e", BROWSER_CHECK],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
            )
            try:
                process.stdin.write(json.dumps({"url": f"http://127.0.0.1:{server.server_port}",
                                                "tokens": server.tokens,
                                                "screenshots": str(screenshots)}) + "\n")
                process.stdin.flush()
                for line in process.stdout:
                    if line.strip() == "OWNER_CODE_REQUIRED":
                        process.stdin.write(server.agent.issue_code() + "\n")
                        process.stdin.flush()
                    else:
                        print(line, end="")
                return process.wait(timeout=10)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                process.stdin.close()
                process.stdout.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    raise SystemExit(main())
