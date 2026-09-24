export default async function run(page, ui) {
  const result = {};

  const snap = await ui.snapshot();
  const user = snap.match(/@(e\d+) textbox "Username"/)?.[1];
  const pass = snap.match(/@(e\d+) textbox "Password"/)?.[1];
  const signIn = snap.match(/@(e\d+) button "Sign In"/)?.[1];
  if (!user || !pass || !signIn) return { error: 'login form not found', snap };

  await ui.fill(user, 'admin');
  await ui.fill(pass, 'admin123');
  await ui.click(signIn);

  // Wait for navigation to dashboard and app content to load
  await page.waitForTimeout(3000);

  // Wait for the "Sample App" card text if present
  let appLoaded = false;
  for (let i = 0; i < 10; i++) {
    const txt = await page.evaluate(() => document.body.innerText);
    if (txt.includes('Sample App')) { appLoaded = true; break; }
    await page.waitForTimeout(1000);
  }

  result.appLoaded = appLoaded;
  result.url = page.url();
  result.text = (await page.evaluate(() => document.body.innerText)).slice(0, 1500);
  return result;
}
