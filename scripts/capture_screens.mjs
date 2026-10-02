import { chromium } from 'playwright-core';
import fs from 'fs';
import path from 'path';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BASE_URL = 'http://127.0.0.1:5000';
const OUT_DIR = path.resolve('showcase/assets/screens');

if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function run() {
  console.log('[Capture] Launching Chromium from:', CHROME_PATH);
  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1920,1080']
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1
  });

  const page = await context.newPage();

  // Helper to safely navigate hash routes and wait for content
  async function visitAndCapture(hash, filename, delay = 1500) {
    console.log(`[Capture] Navigating to ${BASE_URL}/${hash}...`);
    await page.goto(`${BASE_URL}/${hash}`, { waitUntil: 'networkidle' });
    await sleep(delay);
    const dest = path.join(OUT_DIR, filename);
    await page.screenshot({ path: dest, fullPage: false });
    const stat = fs.statSync(dest);
    console.log(`[Capture] Saved ${filename} (${Math.round(stat.size / 1024)} KB)`);
  }

  // Helper to login via UI
  async function login(email, password) {
    console.log(`[Capture] Logging in as ${email}...`);
    await page.goto(`${BASE_URL}/#/auth`, { waitUntil: 'networkidle' });
    await sleep(1000);

    await page.evaluate(async ({ email, password }) => {
      if (window.ApiClient) {
        await window.ApiClient.login(email, password);
      }
    }, { email, password });

    await page.reload({ waitUntil: 'networkidle' });
    await sleep(1500);
  }

  async function logout() {
    await page.evaluate(async () => {
      if (window.ApiClient) {
        await window.ApiClient.logout();
      }
    });
    await sleep(1000);
  }

  try {
    // 1. Capture Auth Screen
    await page.goto(`${BASE_URL}/#/auth`, { waitUntil: 'networkidle' });
    await sleep(1500);
    await page.screenshot({ path: path.join(OUT_DIR, 'scr_01_auth.png') });
    console.log('[Capture] Saved scr_01_auth.png');

    // 2. Student Flow (student1@pwd301.local)
    await login('student1@pwd301.local', 'Password123!');
    await visitAndCapture('#/student/dashboard', 'scr_02_student_dash.png', 2000);
    await visitAndCapture('#/student/catalog', 'scr_03_catalog.png', 2000);
    await visitAndCapture('#/student/courses/detail?id=1', 'scr_04_course_console.png', 2000);
    await visitAndCapture('#/student/courses/1/lessons/1', 'scr_05_lesson_reader.png', 2000);
    await visitAndCapture('#/student/assessments/waiting-room?id=1', 'scr_06_waiting_room.png', 2000);
    await visitAndCapture('#/student/assessments/attempt?id=1', 'scr_07_exam_attempt.png', 2000);
    await visitAndCapture('#/student/assessments/results?id=1', 'scr_08_exam_results.png', 2000);
    await visitAndCapture('#/student/ai-assistant', 'scr_09_ai_assistant.png', 2000);

    // 3. Instructor Flow (instructor1@pwd301.local)
    await logout();
    await login('instructor1@pwd301.local', 'Password123!');
    await visitAndCapture('#/instructor/dashboard', 'scr_10_instructor_dash.png', 2000);
    await visitAndCapture('#/instructor/courses/manage?id=1', 'scr_11_curriculum.png', 2000);
    await visitAndCapture('#/instructor/courses/1/lessons/new', 'scr_12_lesson_studio.png', 2000);
    await visitAndCapture('#/instructor/exams/hub', 'scr_13_exam_hub.png', 2000);
    await visitAndCapture('#/instructor/exams/matrix', 'scr_14_exam_matrix.png', 2000);

    // 4. Admin Flow (admin@pwd301.local)
    await logout();
    await login('admin@pwd301.local', 'Password123!');
    await visitAndCapture('#/admin/governance?tab=users', 'scr_15_admin_users.png', 2000);
    await visitAndCapture('#/admin/courses/review?id=3', 'scr_16_course_review.png', 2000);
    await visitAndCapture('#/admin/operations', 'scr_17_telemetry.png', 2000);

    console.log('[Capture] All 17 authentic screens captured successfully!');
  } catch (err) {
    console.error('[Capture Error]', err);
  } finally {
    await browser.close();
  }
}

run();
