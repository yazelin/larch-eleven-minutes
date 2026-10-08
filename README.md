# 十一分鐘

Larch 第三屆創作者挑戰《自由與限制》第二部投稿（第一部是《起跑總在開始前》）。十月九日 23:47，防火長城開了十一分鐘。

- 原文：`canon/原文.md`（遊戲裡的句子一律從這裡讀）；新寫句子：`canon/新寫.md`（`##` 標題是程式取用的鍵）；介紹文：`canon/介紹文.md`
- 規格：`docs/specs/2026-10-08-design.md`
- Larch 專案：`project-fc97ad09-681c-47f9-80b9-e12753877b9c`（還沒推內容，先在本機 larch-preview 驗）

## 結構

| 檔案 | 內容 |
|---|---|
| `src/build.py` | 組出 `dist/project.json`：序章卡 → 十九樓地圖 → 審訊室卡（`BLOCKS=1` 換成單色塊版） |
| `src/map_office.py` | 十九樓事件：開場、周主任下令、監控台、茶水間、警衛擋人、抽屜、樓梯門；任務提示 |
| `src/story.py` | 讀原文與新寫 |
| `src/layout.py`、`art/objects_<地圖>.yaml` | 分層地圖設計檔（照《香布纏．續》：佔地、往上長、排序列） |
| `art/blocks.py`、`art/compose.py` | 單色塊驗證圖、構圖圖 |
| `art/objects_gen.py` | 物件與地面產圖、去背、擺放（走 .11 codex-image，`art/codex11.py`） |
| `art/walk.py` | 走路圖（沿用《續》的 walk.py） |
| `art/anchor/` | 九個王戰角色定錨 |

## 指令

    python3 src/build.py                                  # 產出 dist/project.json
    python3 ~/larch-preview/serve.py dist/project.json    # 本機播放
    python3 tests/check_static.py                         # 原文全用上、id 唯一、引擎上限
    node tests/play_office.mjs                            # 十九樓從序章玩到樓梯門（約 3 分鐘）
    node tests/guard_stop.mjs                             # 警衛擋人＋對照組
    node tests/layer_shots.mjs                            # 分層遮擋截圖
