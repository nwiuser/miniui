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
  await page.waitForTimeout(2500);

  result.afterSignIn = await ui.snapshot();
  return result;
}
