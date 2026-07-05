#!/usr/bin/env python3
"""Build a Korean word dataset for the brainrot word test.

This script uses the official Urimalsaem Open API from the National Institute
of Korean Language. It does not scrape Naver Dictionary or undocumented APIs.

Usage:
  1) Get an API key from https://opendict.korean.go.kr/service/openApiInfo
  2) Set the key:
       macOS/Linux: export URIMALSAEM_API_KEY="your_key"
       Windows PS:  $env:URIMALSAEM_API_KEY="your_key"
  3) Run:
       python scripts/build_korean_dataset.py

Outputs:
  - korean_words_full.json
  - korean_words_full.csv
"""

from __future__ import annotations

import csv
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Set

API_URL = "https://opendict.korean.go.kr/api/search"
ROOT = Path(__file__).resolve().parents[1]
CUSTOM_WORDS_PATH = ROOT / "custom_words.csv"
OUT_JSON = ROOT / "korean_words_full.json"
OUT_CSV = ROOT / "korean_words_full.csv"

# The full syllable range is huge. For a first useful dataset, start with common
# initial syllables. Add/remove syllables here when you want a larger build.
SEED_SYLLABLES = """
가 각 간 갈 감 갑 강 개 객 갱 거 건 걸 검 겁 것 게 겨 격 견 결 겸 경 계 고 곡 곤 골 공 과 관 광 괴 교 구 국 군 굴 궁 권 귀 규 균 그 극 근 글 금 급 긍 기 긴 길 김 깃 까 깍 깔 깨 꺼 꼬 꽃 꾸 꿈 끝
나 낙 난 날 남 납 낭 내 냉 너 넉 널 넘 네 녀 년 노 녹 논 놀 농 뇌 누 눈 눌 뉴 느 늑 는 늘 능 니 님
다 단 달 담 답 당 대 댁 더 덕 덜 덤 데 도 독 돈 돌 동 돼 되 두 둑 둔 뒤 드 득 들 등 디 따 땅 때 떡 또 똑 뚜 뜻
라 락 란 람 랑 래 량 러 레 력 련 렬 령 례 로 록 론 롤 료 루 류 륙 률 륭 르 름 리 린 림 립
마 막 만 말 맛 망 매 맥 맨 머 먹 멋 메 면 멸 명 모 목 몫 몸 못 몽 무 묵 문 물 미 민 밀 밑
바 박 반 발 밤 밥 방 배 백 번 벌 범 법 베 벽 변 별 병 보 복 본 볼 봄 봉 부 북 분 불 붕 비 빈 빛 빵 뼈 뿌
사 삭 산 살 삼 상 새 색 생 서 석 선 설 섬 성 세 셈 소 속 손 솔 솜 송 쇠 수 숙 순 술 숨 숲 쉬 습 승 시 식 신 실 심 십 쌀 씨
아 악 안 알 암 압 앙 애 액 야 약 양 어 억 언 얼 엄 업 에 여 역 연 열 염 영 예 오 옥 온 올 옴 옷 와 완 왕 왜 외 요 욕 용 우 운 울 움 웃 원 월 위 유 육 율 은 음 의 이 익 인 일 임 입 잎
자 작 잔 잘 잠 장 재 쟁 저 적 전 절 점 접 정 제 조 족 존 졸 종 좌 죄 주 죽 준 줄 중 쥐 즈 즉 즐 증 지 직 진 질 짐 집 징 짝 쪽 찌
차 착 찬 찰 참 창 채 책 처 척 천 철 첨 첫 청 체 초 촉 촌 총 최 추 축 춘 출 충 취 층 치 친 칠 침 칭
카 칸 칼 캐 커 컵 케 코 콩 쾌 쿠 퀴 크 큰 클 키
타 탁 탄 탈 탐 탑 탕 태 택 터 턱 털 테 토 통 퇴 투 특 틀 티
파 판 팔 패 팬 퍼 페 편 평 폐 포 폭 표 푸 풍 프 피 필 핑
하 학 한 할 함 합 항 해 핵 행 향 허 헌 험 헤 혁 현 혈 혐 형 혜 호 혹 혼 홀 홍 화 확 환 활 황 회 획 효 후 훈 훌 훔 훼 휘 휴 흉 흐 흑 흔 흙 흠 흡 흥 희 힘
""".split()

CUSTOM_DEFAULT_WORDS = ["울음", "인정", "충청도"]
HANGUL_RE = re.compile(r"^[가-힣]{2,}$")
INITIALS = ["ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]


def get_initial(word: str) -> str:
    code = ord(word[0]) - 44032
    if code < 0 or code > 11171:
        return ""
    return INITIALS[code // 588]


def clean_word(word: str) -> str:
    word = str(word or "").strip().replace("-", "").replace("^", "")
    word = re.sub(r"\(.+?\)", "", word)
    word = re.sub(r"\s+", "", word)
    return word if HANGUL_RE.match(word) else ""


def load_custom_words() -> List[str]:
    if not CUSTOM_WORDS_PATH.exists():
        with CUSTOM_WORDS_PATH.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["word", "source", "note"])
            for word in CUSTOM_DEFAULT_WORDS:
                writer.writerow([word, "manual", "initial missing words"])
    words: List[str] = []
    with CUSTOM_WORDS_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = clean_word(row.get("word", ""))
            if cleaned:
                words.append(cleaned)
    return words


def request_json(params: Dict[str, str | int]) -> Dict:
    query = urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(f"{API_URL}?{query}", headers={"User-Agent": "brainrot-word-builder/1.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_items(payload: Dict) -> List[Dict]:
    channel = payload.get("channel", {})
    items = channel.get("item", [])
    if isinstance(items, dict):
        return [items]
    return items if isinstance(items, list) else []


def fetch_words_for_prefix(api_key: str, prefix: str, max_pages: int = 10, sleep_sec: float = 0.08) -> Set[str]:
    words: Set[str] = set()
    start = 1
    num = 100

    for _ in range(max_pages):
        payload = request_json({
            "key": api_key,
            "q": prefix,
            "req_type": "json",
            "part": "word",
            "sort": "dict",
            "advanced": "y",
            "target": 1,
            "method": "start",
            "type1": "word",
            "type3": "general",
            "type4": "general",
            "pos": 1,
            "letter_s": 2,
            "letter_e": 6,
            "start": start,
            "num": num,
        })

        items = extract_items(payload)
        for item in items:
            word = clean_word(item.get("word", ""))
            if word:
                words.add(word)

        total = int(payload.get("channel", {}).get("total", 0) or 0)
        start += num
        if not items or start > total or start > 1000:
            break
        time.sleep(sleep_sec)

    return words


def add_words(groups: Dict[str, Set[str]], words: Iterable[str]) -> None:
    for word in words:
        initial = get_initial(word)
        if initial:
            groups.setdefault(initial, set()).add(word)


def main() -> None:
    api_key = os.environ.get("URIMALSAEM_API_KEY")
    if not api_key:
        raise SystemExit("Set URIMALSAEM_API_KEY first. See script header for usage.")

    groups: Dict[str, Set[str]] = {initial: set() for initial in INITIALS}
    add_words(groups, load_custom_words())

    total_prefixes = len(SEED_SYLLABLES)
    for index, prefix in enumerate(SEED_SYLLABLES, 1):
        try:
            words = fetch_words_for_prefix(api_key, prefix)
            add_words(groups, words)
            print(f"[{index:>3}/{total_prefixes}] {prefix}: +{len(words)}")
        except Exception as exc:
            print(f"[{index:>3}/{total_prefixes}] {prefix}: ERROR {exc}")
            time.sleep(1)

    json_data = {initial: sorted(words) for initial, words in groups.items() if words}
    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["chosung", "word"])
        for initial, words in json_data.items():
            for word in words:
                writer.writerow([initial, word])

    print(f"Done: {sum(len(words) for words in json_data.values())} words")
    print(f"Wrote: {OUT_JSON.name}, {OUT_CSV.name}")


if __name__ == "__main__":
    main()
