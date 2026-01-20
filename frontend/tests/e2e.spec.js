const { test, expect } = require("@playwright/test");

test.describe("Nai-Balance UI", () => {
  test("login and view client keys", async ({ page }) => {
    await page.goto("http://localhost:5002");

    await page.locator("#loginForm input[name='username']").fill("test");
    await page.locator("#loginForm input[name='password']").fill("test123");
    await page.locator("#loginForm button[type='submit']").click();

    await expect(page.locator("#authStatus")).toContainText("已登录");

    await page.locator(".nav-item[data-section='keys']").click();
    await expect(page.locator("#clientKeysTable")).toBeVisible();
  });
});
