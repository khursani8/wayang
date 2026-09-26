# Remotion + VOICEVOX 動画作成スキル

ずんだもん＆めたんの掛け合い紹介動画を作成するためのスキルです。

## このスキルを使うタイミング

- ユーザーが「紹介動画を作りたい」「解説動画を作りたい」と言った
- ユーザーが「ずんだもん」「めたん」「VOICEVOX」に言及した
- プロジェクトに `src/data/script.ts` が存在する
- ユーザーが「音声を生成して」「動画を出力して」と言った

---

## 重要: コンテンツ表示のルール

**コンテンツは画面全体を使って最大限大きく表示する。無駄な余白は作らない。**

### 基本方針
- スクリーンショットや図解は**画面いっぱいに表示**
- 不要なパディングやマージンを入れない
- 字幕とキャラクターはコンテンツの上に重ねて表示（下部のみ）
- コンテンツが見切れる場合のみ、必要最小限の余白を設ける

### コンテンツ配置の優先順位
1. **コンテンツを画面全体に表示**（最優先）
2. 字幕は画面下部に重ねて表示
3. キャラクターは左右下端に重ねて表示

### 実装時の注意
- 画像・動画は `width: 100%` または `height: 100%` でフィット
- 上下左右の余白は原則0px
- 字幕が重要な情報を隠す場合のみ、コンテンツを上にずらす

---

## プロジェクト構成

```
├── src/
│   ├── data/script.ts       # ★ セリフデータ（主に編集）
│   ├── config.ts            # 動画・キャラクター設定
│   ├── Main.tsx             # メインコンポーネント
│   └── components/
│       ├── Character.tsx    # キャラクター表示・口パク
│       ├── Subtitle.tsx     # 字幕（袋文字）
│       └── SceneVisuals.tsx # シーン別ビジュアル
├── public/
│   ├── images/              # キャラクター画像
│   └── voices/              # 音声ファイル
└── out/video.mp4            # 出力動画
```

---

## セリフデータの形式

### ファイル: `src/data/script.ts`

```typescript
export interface ScriptLine {
  id: number;               // ユニークID（連番）
  character: "zundamon" | "metan";
  text: string;             // 音声生成用（カタカナ可）
  displayText?: string;     // 字幕用（英語表記など、省略可）
  scene: number;            // シーン番号
  voiceFile: string;        // 例: "01_zundamon.wav"
  durationInFrames: number; // 音声生成後に更新
  pauseAfter: number;       // セリフ後の間（フレーム数）
  emotion?: string;         // "normal" | "happy" | "surprised" | "thinking"
}
```

---

## キャラクター設定

| character | 名前 | VOICEVOX Speaker ID | 画面位置 |
|-----------|------|---------------------|----------|
| metan | 四国めたん | 2 | 左下 |
| zundamon | ずんだもん | 3 | 右下 |

### 口調の特徴

**ずんだもん（説明役）**:
- 語尾: 「〜なのだ！」「〜のだ」
- 性格: 元気、明るい、好奇心旺盛

**めたん（聞き役・ツッコミ）**:
- 語尾: 「〜わ」「〜ね」「〜かしら？」
- 性格: 落ち着いた、大人っぽい、質問上手

---

## 英語の発音問題（重要）

VOICEVOXは英語を正しく発音できません。`text`にカタカナ、`displayText`に英語を設定：

```typescript
{
  text: "ホームブルーでインストールするのだ！",      // 音声用
  displayText: "Homebrewでインストールするのだ！", // 字幕用
}
```

### よく使う変換

| 英語 | カタカナ |
|------|---------|
| macOS | マックオーエス |
| iPhone | アイフォン |
| GitHub | ギットハブ |
| API | エーピーアイ |
| AI | エーアイ |
| Homebrew | ホームブルー |
| Ctrl+S | コントロールプラスエス |
| IME | アイエムイー |

---

## 音声生成

### VOICEVOX API

```bash
# 起動確認
curl -s http://localhost:50021/version

# 音声生成
TEXT="セリフ"
SPEAKER=3  # ずんだもん=3, めたん=2
curl -s "http://localhost:50021/audio_query?speaker=${SPEAKER}&text=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$TEXT'))")" -X POST | \
  curl -s "http://localhost:50021/synthesis?speaker=${SPEAKER}" -X POST -H "Content-Type: application/json" -d @- -o output.wav
```

### durationInFrames計算

```
durationInFrames = 音声秒数 × 30fps × 1.2playbackRate
```

---

## コマンド

| コマンド | 説明 |
|---------|------|
| `npm start` | プレビュー（http://localhost:3000） |
| `npm run voices` | 音声一括生成 |
| `npm run build` | 動画出力（out/video.mp4） |
| `npm run init` | 新規プロジェクト初期化 |
| `npm run sync-settings` | YAML設定を反映 |
| `npm run editor` | GUIエディター起動（http://localhost:3001） |

---

## GUIエディターAPI（Claude Code連携用）

GUIエディターのAPIを使用して、ファイルを直接読み書きせずにスクリプトを操作できます。
APIを使用するとtoken消費を抑えられます。

### 起動

```bash
npm run editor:install  # 初回のみ
npm run editor          # http://localhost:3002 でAPI起動
```

### メタデータ取得（token節約）

```bash
curl http://localhost:3002/api/metadata/all
```

レスポンス例：
```json
{
  "characters": [
    { "id": "zundamon", "name": "ずんだもん", "speakerId": 3 },
    { "id": "metan", "name": "四国めたん", "speakerId": 2 }
  ],
  "emotions": {
    "zundamon": ["normal"],
    "metan": ["normal"]
  },
  "animations": ["none", "fadeIn", "slideUp", "slideLeft", "zoomIn", "bounce"],
  "visualTypes": ["none", "image", "text"]
}
```

### スクリプト操作

```bash
# 全スクリプト取得
curl http://localhost:3002/api/script

# 特定行取得
curl http://localhost:3002/api/script/1

# 行更新
curl -X PUT http://localhost:3002/api/script/1 \
  -H "Content-Type: application/json" \
  -d '{"text": "新しいセリフなのだ！"}'

# 新規行追加
curl -X POST http://localhost:3002/api/script \
  -H "Content-Type: application/json" \
  -d '{"character": "zundamon", "text": "追加セリフなのだ！", "scene": 1, "durationInFrames": 60, "pauseAfter": 15}'

# 行削除
curl -X DELETE http://localhost:3002/api/script/5
```

### 設定操作

```bash
# 設定取得
curl http://localhost:3002/api/settings

# 設定更新（sync-settings自動実行）
curl -X PUT http://localhost:3002/api/settings \
  -H "Content-Type: application/json" \
  -d '{"font": {...}, "colors": {...}, ...}'
```

### アクション実行

```bash
# 音声生成
curl -X POST http://localhost:3002/api/actions/generate-voices

# 動画ビルド
curl -X POST http://localhost:3002/api/actions/build-video
```

---

## コンテンツ表示（visual）

セリフごとに画像やテキストを表示：

```typescript
{
  id: 3,
  text: "これがインストール画面なのだ！",
  visual: {
    type: "image",
    src: "install-screen.png",  // public/content/内
    animation: "fadeIn",  // fadeIn, slideUp, slideLeft, zoomIn, bounce
  },
}
```

テキスト表示：
```typescript
{
  visual: {
    type: "text",
    text: "ポイント",
    fontSize: 72,
    animation: "bounce",
  },
}
```

---

## BGM・効果音

BGM設定（script.ts）：
```typescript
export const bgmConfig: BGMConfig = {
  src: "background.mp3",  // public/bgm/
  volume: 0.3,
  loop: true,
};
```

効果音（セリフごと）：
```typescript
{
  se: {
    src: "point.mp3",  // public/se/
    volume: 0.8,
  },
}
```

### 効果音の使い方ガイドライン

- 効果音は**ここぞというところ**で使用（多用しない）
- 1動画で5〜10個程度が目安
- 重要なポイントや感情の変化で使う

### おすすめ効果音（効果音ラボから入手）

| 用途 | ファイル名 | 効果音ラボでの名前 |
|------|-----------|-------------------|
| ポイント強調 | `point.mp3` | 「ポップアップ1」 |
| 正解・成功 | `correct.mp3` | 「正解2」 |
| 驚き | `surprise.mp3` | 「びっくり」 |
| 注目 | `attention.mp3` | 「シャキーン」 |

詳細は `docs/sound-effects-guide.md` を参照。

---

## video-settings.yaml（スタイル設定）

動画のスタイルは `video-settings.yaml` で設定：

```yaml
# フォント設定
font:
  family: "Noto Sans JP"      # フォント名
  size: 48                     # フォントサイズ
  weight: "bold"               # 太さ
  color: "character"           # "character" または "#ffffff" など
  outlineColor: "#000000"      # 外側アウトライン色
  innerOutlineColor: "#ffffff" # 内側アウトライン色

# 字幕設定
subtitle:
  bottomOffset: 40             # 画面下からの距離
  maxWidthPercent: 55          # 最大幅（%）

# キャラクター設定
character:
  height: 367                  # キャラクターの高さ
  useImages: false             # true: 画像使用, false: プレースホルダー

# カラー設定
colors:
  zundamon: "#059669"          # ずんだもん色
  metan: "#db2777"             # めたん色
```

設定変更後は `npm start` で自動反映される。

---

## 動画構成のテンプレート

### セリフの流れ

```
ずんだもん: 〇〇を紹介するのだ！
めたん: それは何かしら？
ずんだもん: △△ができるのだ！
めたん: 便利ね。どうやって使うの？
ずんだもん: こうするのだ！
めたん: なるほど、簡単ね
ずんだもん: みんなも使ってみてほしいのだ！
めたん: それじゃあまたね
二人: バイバイ〜！（声を合わせて）
```

### 最後の「バイバイ」の実装

二人で声を合わせる場合、めたんの後すぐにずんだもんのセリフを入れる：

```typescript
{
  id: 44,
  character: "metan",
  text: "バイバイ〜！",
  voiceFile: "44_metan.wav",
  durationInFrames: 50,
  pauseAfter: 0,  // 間を0にして同時感
},
{
  id: 45,
  character: "zundamon",
  text: "バイバイなのだ〜！",
  voiceFile: "45_zundamon.wav",
  durationInFrames: 60,
  pauseAfter: 60,
},
```

---

## 画像・動画素材の収集

### キャラクター画像
キャラクター画像（立ち絵）はユーザーが手動で入手・配置する。自動取得は行わない。

### 解説に必要な素材
動画の解説で必要なスクリーンショットや動画クリップがある場合、スクリプト作成時にコメントで記載する：

```typescript
{
  id: 5,
  character: "zundamon",
  text: "こんな感じでインストールするのだ！",
  scene: 2,
  voiceFile: "05_zundamon.wav",
  durationInFrames: 100,
  pauseAfter: 10,
  // <<ターミナルでbrew installを実行している画面のスクリーンショット>>
},
```

### 記載フォーマット
```
<<○○の画像>>
<<○○のスクリーンショット>>
<<○○の動画クリップ>>
```

ユーザーの要望があれば、WebSearchで素材の入手先を調べることもできる。

---

## 新規プロジェクト作成

```bash
git clone https://github.com/nyanko3141592/remotion-voicevox-template.git my-video
cd my-video
npm install
```

---

## キャラクター画像の構成

### フォルダ構造
```
{imagesBasePath}/{characterId}/
├── mouth_open.png      # 通常表情・口開き（必須）
├── mouth_close.png     # 通常表情・口閉じ（必須）
├── happy_open.png      # happy表情・口開き
├── happy_close.png     # happy表情・口閉じ
├── surprised_open.png  # surprised表情
├── surprised_close.png
├── thinking_open.png   # thinking表情
├── thinking_close.png
├── sad_open.png        # sad表情
└── sad_close.png
```

### 表情差分の使い方

**基本ルール:**
- 基本は`normal`（口パク）で話す
- 表情差分は**多用しない**、ここぞというところで使用
- リアクションは最低0.5秒（15フレーム）継続させる

**使いどころ:**
- 驚いたとき → `surprised`
- 嬉しいとき、褒めるとき → `happy`
- 考え込むとき、説明を聞くとき → `thinking`
- 残念なとき → `sad`

```typescript
// NG: 表情を多用しすぎ
{ text: "すごいのだ！", emotion: "happy" },
{ text: "便利なのだ！", emotion: "happy" },
{ text: "簡単なのだ！", emotion: "happy" },

// OK: ここぞというところで使う
{ text: "すごいのだ！", emotion: "normal" },
{ text: "便利なのだ！", emotion: "normal" },
{ text: "これが一番のポイントなのだ！", emotion: "happy" },  // ← ここぞで使用
```

### 画像パスの設定
`video-settings.yaml`で画像のベースパスを指定可能：
```yaml
character:
  imagesBasePath: "images"  # public/images/{characterId}/
  # または絶対パスで共有フォルダを指定
  # imagesBasePath: "/path/to/shared/characters"
```

---

## キャラクター画像の入手

公式の立ち絵素材を使用する場合：

| キャラクター | 入手先 |
|-------------|--------|
| ずんだもん | https://zunko.jp/con_illust.html |
| 四国めたん | https://zunko.jp/con_illust.html |

ニコニ・コモンズで「ずんだもん 立ち絵」「四国めたん 立ち絵」で検索も可能。

**注意**: 各素材の利用規約を確認してください。

テンプレートにはシンプルなプレースホルダー画像が含まれています。
