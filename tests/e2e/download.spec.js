const { test, expect, _electron: electron } = require('@playwright/test');

let electronApp;

test.beforeAll(async () => {
  // Launch the Electron app
  electronApp = await electron.launch({ args: ['src/main/main.js'] });
});

test.afterAll(async () => {
  // Close the app
  await electronApp.close();
});

test('Main Download Flow', async () => {
  // Get the first window that the app opens
  const window = await electronApp.firstWindow();
  
  // Wait for the window to be visible
  await window.waitForSelector('h1');

  // --- 1. Navigate to Download View and input novel ID ---
  // The app starts in the download view, so no navigation is needed.
  await window.fill('input[type="text"]', '123456');

  // --- 2. Click download button ---
  await window.click('button:has-text("下载")');

  // --- 3. Verify progress ---
  // Wait for the progress bar to appear. This indicates the download has started.
  await window.waitForSelector('.progress-bar', { timeout: 15000 });
  
  // Check that the progress bar is visible
  const progressBar = await window.locator('.progress-bar');
  await expect(progressBar).toBeVisible();

  // --- 4. Wait for completion and verify success status ---
  // In a real E2E test, we'd mock the backend to control the timing.
  // Here, we'll just wait for a reasonable amount of time for the "success" message.
  await window.waitForSelector('.status-message.success', { timeout: 60000 }); // 60s timeout for download
  
  const successMessage = await window.locator('.status-message.success');
  await expect(successMessage).toHaveText('下载完成');

  // --- 5. Navigate to history and verify ---
  await window.click('nav a:has-text("历史")');
  await window.waitForSelector('h1:has-text("下载历史")');
  
  const historyTable = await window.locator('table');
  await expect(historyTable).toContainText('123456'); 
});