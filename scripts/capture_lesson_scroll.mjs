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
  
  await page.goto('http://127.0.0.1:5000/#/student/courses/detail?id=5da5cfbc-28a5-4db8-a478-f634676f2c67');
  await page.waitForTimeout(2500);

  // Scroll down to the rich markdown text and code blocks
  await page.evaluate(() => {
    window.scrollBy({ top: 750, behavior: 'instant' });
    const scrollContainer = document.querySelector('.overflow-y-auto, main, #app-viewport');
    if (scrollContainer) scrollContainer.scrollTop = 750;
  });
  await page.waitForTimeout(1000);

  await page.screenshot({ path: 'showcase/assets/screens/scr_05_lesson_reader.png' });
  console.log('Saved authentic scr_05_lesson_reader.png with scrolled markdown content');
  await browser.close();
}

run();
