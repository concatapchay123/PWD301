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
  
  // 1. Visit Course Console using real course UUID
  await page.goto('http://127.0.0.1:5000/#/student/courses/detail?id=5da5cfbc-28a5-4db8-a478-f634676f2c67');
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'showcase/assets/screens/scr_04_course_console.png' });
  console.log('Successfully captured authentic scr_04_course_console.png');

  // 2. Find and click first lesson link
  const lessonHref = await page.evaluate(() => {
    const l = document.querySelector('a[href*="/lessons/"]');
    return l ? l.href : null;
  });
  console.log('Lesson href found:', lessonHref);

  if (lessonHref) {
    await page.goto(lessonHref);
    await page.waitForTimeout(2500);
    await page.screenshot({ path: 'showcase/assets/screens/scr_05_lesson_reader.png' });
    console.log('Successfully captured authentic scr_05_lesson_reader.png');
  }

  await browser.close();
}

run();
