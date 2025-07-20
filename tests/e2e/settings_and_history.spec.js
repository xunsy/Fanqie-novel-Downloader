const { test, expect, _electron: electron } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

let electronApp;
const tempSettingsPath = path.join(__dirname, 'temp_settings.json');

test.beforeAll(async () => {
  // Launch the Electron app
  electronApp = await electron.launch({ args: ['src/main/main.js'] });
});

test.afterAll(async () => {
  // Close the app
  await electronApp.close();
  // Clean up temp files
  if (fs.existsSync(tempSettingsPath)) {
    fs.unlinkSync(tempSettingsPath);
  }
});

test.describe('Settings and History Flow', () => {
  let window;

  test.beforeEach(async () => {
    window = await electronApp.firstWindow();
    await window.waitForSelector('h1');
  });

  test('Settings Change Flow', async () => {
    // --- 1. Navigate to Settings ---
    await window.click('nav a:has-text("设置")');
    await window.waitForSelector('h1:has-text("设置")');

    // --- 2. Change download path ---
    const newPath = '/new/test/path';
    await window.fill('input#savePath', newPath);

    // --- 3. Save settings ---
    await window.click('button:has-text("保存")');

    // --- 4. Verify success message ---
    const successMessage = await window.locator('.status-message.success');
    await expect(successMessage).toHaveText('设置已保存！');

    // --- 5. Reload and verify the path is persistent ---
    // This requires coordination with the backend, which we can't directly do here.
    // Instead, we trust the success message and assume the backend works as tested in integration tests.
    // A full E2E would require mocking the file system or checking the config file.
    await window.reload();
    await window.waitForSelector('h1:has-text("设置")');
    const savePathInput = await window.locator('input#savePath');
    await expect(savePathInput).toHaveValue(newPath);
  });

  test('History and Redownload Flow', async () => {
    // --- 1. Go to download page and start a download ---
    await window.click('nav a:has-text("下载")');
    await window.fill('input[type="text"]', '78901');
    await window.click('button:has-text("下载")');
    await window.waitForSelector('.status-message.success', { timeout: 60000 });

    // --- 2. Navigate to History page ---
    await window.click('nav a:has-text("历史")');
    await window.waitForSelector('h1:has-text("下载历史")');

    // --- 3. Verify the new record is in the table ---
    const historyRow = await window.locator('table tbody tr', { hasText: '78901' });
    await expect(historyRow).toBeVisible();

    // --- 4. Click redownload ---
    await historyRow.locator('button.redownload-btn').click();

    // --- 5. Verify that we are navigated back to the download page and progress starts ---
    await window.waitForSelector('h1:has-text("下载小说")');
    const progressBar = await window.locator('.progress-bar');
    await expect(progressBar).toBeVisible({ timeout: 15000 });
  });
});