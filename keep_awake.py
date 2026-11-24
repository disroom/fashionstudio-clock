# -*- coding: utf-8 -*-
"""늘 켜진 주소를 **사람처럼 한 번 열어 본다.**

    python keep_awake.py
    python keep_awake.py --url https://…/~/+/ --hold 30

왜 `curl` 로는 안 되나
----------------------
스트림릿 공용 클라우드는 방문이 **12시간** 없으면 앱을 재운다. 그런데 잠든 앱에
평범한 HTTP 요청을 보내면 **200 을 주면서 계속 잔다** — 받는 것은 껍데기 HTML 이고,
깨우는 것은 그 뒤에 자바스크립트가 여는 **웹소켓**(`/_stcore/stream`)이다.

그래서 진짜 브라우저로 연다. 열고, 화면이 그려질 때까지 기다리고, 잠들어 있었으면
「Yes, get this app back up!」 을 눌러 주고, 웹소켓이 살아 있도록 잠깐 머물다 나온다.

이 파일은 **혼자 선다** — 파이썬에 들어 있는 것과 `playwright` 말고는 아무것도
필요 없다. 여는 주소는 **누구나 볼 수 있는 공개 주소**다.
"""
from __future__ import annotations

import argparse
import sys
import time

DEFAULT_URL = "https://fashionstudio.streamlit.app/~/+/"

# 화면이 떴다고 볼 표시. 테넌트가 바뀌어도 걸리도록 여러 개를 본다.
#   1124: 비공개 쪽 사본이 보던 이름들(DK Studio AI · MIND_PRINT)을 합쳤다.
#   둘을 하나로 모으면서 **넓은 쪽**을 남긴다 — 좁은 쪽을 남기면 테넌트를
#   바꾼 날 「화면이 안 떴다」고 틀리게 운다.
떴다 = ("AI STUDIO", "DK Studio AI", "MIND_PRINT", "패션 디자이너 작업실",
        "상품 작업", "패션 트렌드")

# 잠들어 있을 때 나오는 단추
깨우기 = "get this app back up"


def main() -> int:
    ap = argparse.ArgumentParser(description="늘 켜진 주소를 한 번 열어 본다")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--hold", type=int, default=30, help="화면이 뜬 뒤 머무는 초")
    ap.add_argument("--timeout", type=int, default=240, help="깨어나기를 기다릴 최대 초")
    a = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[ERROR] playwright 가 없습니다 — pip install playwright")
        return 1

    t0 = time.time()
    with sync_playwright() as p:
        # 러너에 이미 깔린 크롬을 먼저 쓴다 — 400MB 를 또 받지 않는다.
        # 없거나 안 뜨면 묶여 오는 chromium 으로 내려간다.
        찻길 = ["--no-sandbox", "--disable-dev-shm-usage"]
        br = None
        for 통로 in ("chrome", None):
            try:
                br = (
                    p.chromium.launch(channel=통로, args=찻길)
                    if 통로
                    else p.chromium.launch(args=찻길)
                )
                print("[브라우저] %s" % (통로 or "묶음 chromium"))
                break
            except Exception as e:  # noqa: BLE001
                print("[알림] %s 를 못 띄웠습니다 — %s" % (통로 or "묶음 chromium", e))
        if br is None:
            print("[ERROR] 띄울 수 있는 브라우저가 없습니다")
            return 1

        pg = br.new_page(viewport={"width": 1280, "height": 900})
        print("[열기] %s" % a.url)
        pg.goto(a.url, wait_until="domcontentloaded", timeout=60_000)

        눌렀나 = False
        본것 = ""
        while time.time() - t0 < a.timeout:
            try:
                본것 = pg.inner_text("body", timeout=5_000) or ""
            except Exception:  # noqa: BLE001 — 화면이 아직 없을 수 있다
                본것 = ""
            if any(s in 본것 for s in 떴다):
                break
            if (깨우기 in 본것) and not 눌렀나:
                print("[잠듦] 깨우기 단추를 누릅니다")
                try:
                    pg.get_by_text(깨우기, exact=False).first.click(timeout=10_000)
                    눌렀나 = True
                except Exception as e:  # noqa: BLE001
                    print("[WARN] 단추를 못 눌렀습니다 — %s" % e)
            time.sleep(5)

        걸린 = time.time() - t0
        if not any(s in 본것 for s in 떴다):
            print("[ERROR] %d초 안에 화면이 안 떴습니다 (%.0f초)" % (a.timeout, 걸린))
            print("        받은 글 앞부분: " + " ".join(본것.split())[:200])
            br.close()
            return 1

        print("[OK] 화면이 떴습니다 (%.0f초)%s"
              % (걸린, " · 잠들어 있던 것을 깨웠습니다" if 눌렀나 else ""))
        print("[대기] %d초 머뭅니다" % a.hold)
        time.sleep(a.hold)

        # 1124: **무엇이 떴는지** 한 줄 남긴다. 테넌트가 어긋나면 여기서 보인다.
        #   (비공개 쪽 사본에만 있던 것을 합치면서 가져왔다.)
        print("[화면] %s" % " ".join(본것.split())[:80])
        br.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
