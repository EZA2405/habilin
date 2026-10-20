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
    const link = url + '/';
    async function stage(expected) {
      await page.waitForFunction(expected => document.querySelector('#execution-stage').textContent === expected, expected);
      await page.waitForFunction(() => !document.querySelector('#next-action').disabled);
    }
    async function as(role) {
      await page.locator('#switch-user').click();
      await page.locator(`[data-person=${role}]`).click();
      await page.waitForFunction(role => document.body.dataset.role === role, role);
    }
    async function code(caseId) { console.log('OWNER_CODE_REQUIRED ' + caseId); return (await input.next()).value; }
    async function fits(p) { assert(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Horizontal overflow'); }
    async function approveAll(caseId) {
      await page.locator('#next-action').click();
      await stage('ready_to_prepare');
      assert(await page.locator('#question').isVisible(), 'Question buttons should be visible');
      await page.locator('#answer-no').click();
      await page.waitForFunction(() => document.querySelector('#question').hidden);
      await page.locator('#next-action').click();
      await stage('await_professional');
      await as('professional');
      assert(await page.locator('#approval').isVisible());
      await page.locator('#confirm').check();
      await page.locator('#approve-button').click();
      await stage('await_owner');
      await as('owner');
      assert(await page.locator('#owner-code').isVisible());
      await page.locator('#confirm').check();
      await page.locator('#owner-code').fill(await code(caseId));
      await page.locator('#approve-button').click();
      await stage('ready_to_submit');
      await as('operator');
      for (const next of ['filing_unknown', 'payment_pending', 'completed']) {
        await page.locator('#next-action').click();
        await stage(next);
      }
    }
    await page.goto(link);
    await page.screenshot({path: screenshots + '/tour.png'});
    for (let i = 0; i < 4; i++) await page.locator('#intro-next').click();
    assert.equal(await page.locator('#intro-next').textContent(), 'Start as Maria');
    await page.locator('#intro-next').click();
    await page.waitForFunction(() => document.body.dataset.role === 'operator');
    await stage('missing_record');
    await fits(page);
    await page.screenshot({path: screenshots + '/start-desktop.png', fullPage: true});
    await page.locator('#onb-done').click();
    await page.locator('#chat-toggle').click();
    await page.screenshot({path: screenshots + '/chat-widget.png'});
    await page.locator('#chat-close').click();
    await page.locator('#case-details > summary').click();
    await approveAll('EST-001');
    assert.equal(await page.locator('#payment-receipt').textContent(), 'SIM-PAY-0001');
    assert.equal(await page.locator('#tax-total').textContent(), '₱150,000');
    assert.equal(await page.locator('#office-mailbox').textContent(), 'rdo39_collection@bir.gov.ph');
    assert.equal(await page.locator('#outbox-status').textContent(), 'Draft ready · not sent');
    assert.equal(await page.locator('#m-penalty').textContent(), '₱55,500 avoided');
    await page.locator('[data-tab=office]').click();
    await page.screenshot({path: screenshots + '/completed-offices.png', fullPage: true});
    await page.locator('[data-tab=impact]').click();
    await page.screenshot({path: screenshots + '/completed-impact.png', fullPage: true});
    await as('owner');
    await page.locator('#lock').click();
    await page.locator('#lock').waitFor({state: 'hidden'});
    await page.locator('#close-case').click();
    await page.locator('#close-case').click();
    await stage('closed');
    assert.equal(await page.locator('#case-name').textContent(), 'Closed case EST-001');
    assert.equal(await page.locator('#m-deleted').textContent(), 'Yes');
    assert.equal(await page.locator('#m-mismatch').textContent(), '1');
    await as('operator');
    await page.locator('[data-case="EST-UK-001"]').click();
    await stage('missing_record');
    await approveAll('EST-UK-001');
    assert.equal(await page.locator('#tax-total').textContent(), '£50,000');
    assert.equal(await page.locator('#payment-receipt').textContent(), 'SIM-HMRC-PAY-0001');
    await page.locator('[data-tab=tax]').click();
    await page.screenshot({path: screenshots + '/uk-completed.png', fullPage: true});
    const mobile = await browser.newPage({viewport: {width: 390, height: 844}, reducedMotion: 'reduce'});
    mobile.on('pageerror', error => errors.push(error.message));
    await mobile.goto(link);
    await fits(mobile);
    await mobile.screenshot({path: screenshots + '/mobile-tour.png'});
    await mobile.locator('#intro-skip').click();
    await mobile.locator('[data-person=operator]').click();
    await mobile.waitForFunction(() => document.body.dataset.role === 'operator');
    await fits(mobile);
    await mobile.screenshot({path: screenshots + '/mobile.png', fullPage: true});
    await mobile.close();
    assert.deepEqual(errors, []);
    console.log('PASS: automatic local sign-in, role tabs, family-home question, PH and UK cases end to end, office routing, impact, lock, closure, desktop/mobile layouts; no browser errors.');
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
                    if line.startswith("OWNER_CODE_REQUIRED"):
                        process.stdin.write(server.agent.issue_code(line.split()[1]) + "\n")
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
