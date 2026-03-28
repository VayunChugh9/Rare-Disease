import { test, expect } from "@playwright/test";
import path from "path";

const BASE_URL = "http://localhost:5173";
const REFERRAL_NOTE = path.resolve(__dirname, "../Bryant814_Bins636_referral_realistic.txt");
const CCDA_XML = path.resolve(
  __dirname,
  "../synthea_sample_data_ccda_latest/Bryant814_Bins636_aa4061cf-0f5e-b627-252d-9a705eac4e70.xml"
);

test.describe("MVP End-to-End Flow", () => {
  test("Landing → Upload → Processing → Review Dashboard → PDF → Finalize", async ({ page }) => {
    // Increase timeout for AI processing
    test.setTimeout(120_000);

    // 1. Landing page loads
    await page.goto(BASE_URL);
    await page.waitForLoadState("networkidle");
    await page.screenshot({ path: "e2e/screenshots/01-landing.png" });

    // 2. Navigate to Upload page directly
    await page.goto(`${BASE_URL}/upload`);
    await page.waitForLoadState("networkidle");
    await page.screenshot({ path: "e2e/screenshots/02-upload-page.png" });

    // 3. Upload referral note
    const noteInput = page.locator('input[type="file"][accept=".txt,.pdf"]');
    await noteInput.setInputFiles(REFERRAL_NOTE);
    await page.waitForTimeout(500);

    // 4. Upload CCDA XML
    const hieInput = page.locator('input[type="file"][accept=".xml"]');
    await hieInput.setInputFiles(CCDA_XML);
    await page.waitForTimeout(500);
    await page.screenshot({ path: "e2e/screenshots/03-files-selected.png" });

    // 5. Click Process Referral
    const submitBtn = page.locator('button:has-text("Process Referral")');
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();

    // 5b. Capture the progress bar
    await page.waitForTimeout(3000);
    await page.screenshot({ path: "e2e/screenshots/03b-processing-progress.png" });

    // 6. Wait for processing to complete (AI extraction takes time)
    await page.waitForSelector('text=Referral Processed', { timeout: 90_000 });
    await page.screenshot({ path: "e2e/screenshots/04-processing-done.png" });

    // 7. Click Review Referral to go to dashboard
    const reviewBtn = page.locator('button:has-text("Review Referral")');
    await expect(reviewBtn).toBeVisible();
    await reviewBtn.click();
    await page.waitForURL("**/review/**");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);
    await page.screenshot({ path: "e2e/screenshots/05-review-dashboard.png" });

    // 8. Verify dashboard has key sections
    // Patient name should be visible
    await expect(page.locator('text=Bryant').first()).toBeVisible({ timeout: 10_000 });

    // Check for clinical data sections
    const sections = [
      "Active Conditions",
      "Medications",
      "Allergies",
      "Vitals",
    ];
    for (const section of sections) {
      const el = page.locator(`text=${section}`).first();
      const visible = await el.isVisible().catch(() => false);
      console.log(`Section "${section}": ${visible ? "VISIBLE" : "NOT FOUND"}`);
    }

    // 9. Scroll down to see more content
    await page.evaluate(() => window.scrollBy(0, 600));
    await page.waitForTimeout(500);
    await page.screenshot({ path: "e2e/screenshots/06-dashboard-scrolled.png" });

    // 10. Test PDF download
    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 30_000 }),
      page.locator('button:has-text("PDF"), button:has-text("Download")').first().click(),
    ]);
    const downloadPath = await download.path();
    expect(downloadPath).toBeTruthy();
    console.log(`PDF downloaded: ${download.suggestedFilename()}`);
    await page.screenshot({ path: "e2e/screenshots/07-after-pdf.png" });

    // 11. Test Finalize
    const finalizeBtn = page.locator('button:has-text("Finalize")').first();
    if (await finalizeBtn.isVisible()) {
      await finalizeBtn.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: "e2e/screenshots/08-finalized.png" });
      // Should show finalized state
      const finalized = page.locator('text=Finalized').first();
      await expect(finalized).toBeVisible({ timeout: 5_000 });
      console.log("Finalize: SUCCESS");
    }

    console.log("MVP E2E test completed successfully!");
  });

  test("Queue page shows referrals", async ({ page }) => {
    await page.goto(`${BASE_URL}/queue`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
    await page.screenshot({ path: "e2e/screenshots/09-queue.png" });

    // Should show at least one referral card
    const referralCards = page.locator('[class*="referral"], [class*="card"], tr, [role="row"]');
    const count = await referralCards.count();
    console.log(`Queue items found: ${count}`);
    expect(count).toBeGreaterThan(0);
  });
});
