# 十一分鐘

Larch 第三屆創作者挑戰《自由與限制》第二部投稿（第一部是《起跑總在開始前》）。六月四日 23:49，防火長城開了十一分鐘。

- 原文：`canon/原文.md`（遊戲裡的句子一律從這裡讀）；新寫句子：`canon/新寫.md`（`##` 標題是程式取用的鍵）；介紹文：`canon/介紹文.md`
- 規格：`docs/specs/2026-10-08-design.md`
- 遊玩：https://larch.ink/play/market/yaze/11-minutes
- 公開站：https://yazelin.github.io/larch-eleven-minutes/ （`docs/index.html`；素材 `python3 site/media.py` 從 assets 縮成 `docs/media/`，截圖 `node tests/site_shots.mjs`；頁面裡的圖與音樂走 jsDelivr 孤兒 tag `site-media-1`，換素材要打下一個 tag 再改網址）
- 授權：程式碼 MIT（`LICENSE`），故事、美術、配樂 CC BY-NC-SA 4.0（`LICENSE-CONTENT.md`；大肥魚原型〈溟月〉是 SA）
- Larch 專案：`project-fc97ad09-681c-47f9-80b9-e12753877b9c`（`python3 src/push.py "改了什麼"` 推上去；推之前把 Larch 編輯器分頁關掉，發佈由作者在網頁按）

## 結構

| 檔案 | 內容 |
|---|---|
| `src/build.py` | 組出 `dist/project.json`：序章 → 十九樓 → 二十樓 → 終端機卡 → 雲端長城（王戰、審訊室（二）、三結局）→ 片尾。`BLOCKS=1` 換成單色塊版；還沒產正式圖的地圖自動用色塊。測試用 `START=<卡 id>`、`PRESET=phase=gate,kills=4` |
| `src/map_server.py` | 二十樓核心機房：開場、終端機 |
| `src/map_cloud.py` | 雲端長城：找江禾那一則、審查兵動作戰鬥、門前四場回合制王戰（打輸再按門重打）、鎖鏈崩開與扣回、結局選擇 |
| `src/battles.py` | 戰鬥卡：審查兵、獵犬、第一班、第二班、大肥魚、PRISM（招式名取自原文） |
| `src/plugin.py`、`src/plugin/terminal.html` | 自製插件 `eleven-minutes`：終端機卡（ping、traceroute、sudo wall） |
| `src/map_office.py` | 十九樓事件：開場、周主任下令、監控台、茶水間、警衛擋人、抽屜、樓梯門；任務提示 |
| `src/story.py` | 讀原文與新寫 |
| `src/layout.py`、`art/objects_<地圖>.yaml` | 分層地圖設計檔（照《香布纏．續》：佔地、往上長、排序列） |
| `art/blocks.py`、`art/compose.py` | 單色塊驗證圖、構圖圖 |
| `art/objects_gen.py` | 物件與地面產圖、去背、擺放（走 .11 codex-image，`art/codex11.py`）；同一排的牆連門整排一張生成再切段（`LINES`、`COLS`，照《續》嚴家） |
| `art/walk.py` | 走路圖（沿用《續》的 walk.py） |
| `art/anchor/` | 九個王戰角色定錨 |
| `art/battle_gen.py` | 戰鬥圖：照定錨在綠幕重產再去背 → `assets/battle/` |
| `src/ui/interface.json` | 介面：作者在 Larch 套用的官方「霓虹訊號」（2026-10-09 讀回）；要改哪個部位就放 `src/ui/<部位>.css`／`.html` 蓋過去 |
| `art/scene_gen.py` | 場面圖：標題封面（`assets/cover/title.webp`）、審訊室與三個結局的背景（`assets/scenes/`）；每張寫明在場角色、在場的人一定帶定錨 |
| `art/music.py` | 配樂：.11 gemini-web 作曲 → 60 秒循環、-16 LUFS（`assets/bgm/`）；標題、十九樓、二十樓、雲端、王戰、結局 |
| `art/thumb.py` | 市集縮圖（封面＋霓虹片名字） |
| `src/push.py` | 推上 Larch：快照 → 上傳圖與音樂 → 換網址 → 整包寫入 → 讀回比對（介面、介紹文以網頁上的為準） |
| `docs/過關SOP.md` | 每一關的九步過關流程與進度表 |
| `docs/待辦.md` | 還沒做與可改善的清單（發佈後的改版從這裡挑） |

## 指令

    python3 voice/gen.py                                  # 角色配音（larch-tts-bridge，見 docs/配音表.md）
    python3 voice/review.py                               # 完整劇本＋配音審稿頁 voice/review.html
    python3 src/build.py                                  # 產出 dist/project.json
    python3 ~/larch-preview/serve.py dist/project.json    # 本機播放
    python3 tests/check_static.py                         # 原文全用上、id 唯一、引擎上限
    node tests/play_office.mjs                            # 十九樓從序章玩到樓梯門（約 3 分鐘）
    node tests/guard_stop.mjs                             # 警衛擋人＋對照組
    node tests/stealth.mjs                                # 十九樓潛行：警衛看到會叫回茶水間（對照組拿著碗不會）、周主任轉身時開抽屜會被看到
    node tests/layer_shots.mjs [office|server|cloud]      # 分層遮擋截圖
    node tests/play_rest.mjs [1|2|3]                      # 二十樓到結局（約 12 分鐘，每個結局各跑一次）
    NEG=1 python3 tests/check_static.py                   # 負控制：要失敗
    node tests/mobile_shots.mjs                           # 手機直向、橫向截圖（標題、十九樓、終端機、雲端、王戰）
    node tests/rig_shots.mjs [b-w1|b-w2|b-whale|b-prism]  # 王戰連拍：出手動作與大招插畫
    node tests/talk_shots.mjs b-whale 頂樓那一則          # 戰鬥中途台詞截圖（門檻暫改 99%）
    node tests/ui_shots.mjs                               # 介面截圖：標題、對話卡、地圖、王戰
