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
  
  await page.goto('http://127.0.0.1:5000/#/student/dashboard');
  await page.waitForTimeout(2000);

  const heroHref = await page.evaluate(() => {
    const btn = document.getElementById('hero-continue-lesson-btn');
    return btn ? btn.href : null;
  });
  console.log('Hero Continue Button href:', heroHref);

  if (heroHref) {
    await page.goto(heroHref);
    await page.waitForTimeout(2500);
    await page.screenshot({ path: 'showcase/assets/screens/scr_04_course_console.png' });
    console.log('Saved authentic scr_04_course_console.png');

    // Click on any lesson link inside syllabus
    const lessonLink = page.locator('a[href*="/lessons/"]').first();
    if (await lessonLink.count() > 0) {
      await lessonLink.click();
      await page.waitForTimeout(2500);
      await page.screenshot({ path: 'showcase/assets/screens/scr_05_lesson_reader.png' });
      console.log('Saved authentic scr_05_lesson_reader.png');
    }
  }

  await browser.close();
}

run();
