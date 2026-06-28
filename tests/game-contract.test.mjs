import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");

function extractArray(path) {
  const escaped = path.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = html.match(new RegExp(`${escaped}:\\s*\\[([\\s\\S]*?)\\]`));
  assert.ok(match, `${path} dataset should exist`);
  return [...match[1].matchAll(/"([^"]+)"/g)].map((item) => item[1]);
}

const korWords = ["ㅇ", "ㄱ", "ㅅ"].flatMap((letter) => extractArray(`"${letter}"`));
const engWords = ["f", "a", "s"].flatMap((letter) => extractArray(letter));

assert.ok(html.includes("function getInitialLanguage"), "language detection function should exist");
assert.ok(html.includes("function validateAnswer"), "answer validation function should exist");
assert.ok(html.includes("function shareResult"), "share handler should exist");
assert.ok(html.includes("function copyResultLink"), "copy link handler should exist");
assert.ok(!html.includes('crossorigin="anonymous"></script>'), "script examples inside inline JavaScript must escape closing script tags");
assert.ok(html.includes("data-ad-slot=\"game-bottom\""), "bottom game ad slot should exist");
assert.ok(html.includes("data-ad-slot=\"result-modal\""), "result modal ad slot should exist");
assert.ok(html.includes("GOAL (권장)"), "recommended Korean goal label should exist");
assert.ok(html.includes("건강한 성인의 경우 1분 동안 보통 20~25개 이상의 단어를 떠올리는 것이 정상입니다."), "healthy adult Korean goal explanation should exist");
assert.ok(html.includes("F-A-S Test"), "English F-A-S test explanation should exist");
assert.ok(html.includes("getGoalCount"), "language-aware goal count helper should exist");
assert.ok(html.includes("getResultTier"), "tiered result helper should exist");
assert.ok(html.includes("갓벽한 브레인 스프린터"), "Korean super green tier should exist");
assert.ok(html.includes("Brain Rot Alert"), "English red tier should exist");
assert.ok(korWords.length >= 50, "Korean dataset should include at least 50 words");
assert.ok(engWords.length >= 50, "English dataset should include at least 50 words");
assert.equal(new Set(korWords).size, korWords.length, "Korean dataset should not contain duplicates");
assert.equal(new Set(engWords).size, engWords.length, "English dataset should not contain duplicates");

console.log("Contract tests passed");
