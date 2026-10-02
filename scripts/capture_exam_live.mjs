import { chromium } from 'playwright-core';

async function run() {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--window-size=1920,1080']
  });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  
  await page.goto('http://127.0.0.1:5000/#/auth');
  await page.waitForTimeout(1000);
  await page.evaluate(async () => {
    await window.ApiClient.login('student1@pwd301.local', 'Password123!');
  });
  
  await page.goto('http://127.0.0.1:5000/#/student/assessments');
  await page.waitForTimeout(2000);
  
  const startExamBtn = page.locator('text=Làm bài thi').first();
  await startExamBtn.click();
  await page.waitForTimeout(2000);

  const checkbox = page.locator('input[type="checkbox"]').first();
  if (await checkbox.count() > 0) {
    await checkbox.check();
    await page.waitForTimeout(600);
    const enterBtn = page.locator('button:has-text("Vào thi"), button:has-text("Bắt đầu"), button:has-text("Xác nhận")').first();
    if (await enterBtn.count() > 0) {
      await enterBtn.click();
      await page.waitForTimeout(3000);
    }
  }

  await page.screenshot({ path: 'showcase/assets/screens/scr_07_exam_live_questions.png' });
  console.log('Saved scr_07_exam_live_questions.png');
  await browser.close();
}

run();
