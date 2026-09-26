# Remotion + VOICEVOX 動画テンプレート 詳細ガイド

ずんだもん＆めたんの掛け合い紹介動画を作成するための完全ガイドです。

---

## 目次

1. [クイックスタート](#クイックスタート)
2. [GUIエディター](#guiエディター)
3. [Claude Codeでの使い方](#claude-codeでの使い方)
4. [セリフの書き方](#セリフの書き方)
5. [英語の発音問題](#英語の発音問題)
6. [キャラクター画像](#キャラクター画像)
7. [スタイル設定（video-settings.yaml）](#スタイル設定video-settingsyaml)
8. [手動での使い方](#手動での使い方)
9. [ファイル構成](#ファイル構成)
10. [トラブルシューティング](#トラブルシューティング)
11. [Tips](#tips)

---

## クイックスタート

```bash
# 1. テンプレートをコピー
git clone https://github.com/nyanko3141592/remotion-voicevox-template.git my-video
cd my-video
npm install

# 2. VOICEVOXを起動

# 3. プレビューサーバーを起動
npm start
# → http://localhost:3000 でプレビュー確認

# 4. Claude Codeで開く（別ターミナル）
claude
```

---

## GUIエディター

スクリプトや設定をブラウザから編集できるGUIエディターを搭載しています。

### 起動方法

```bash
# 初回のみ: 依存関係のインストール
npm run editor:install

# エディターを起動
npm run editor
```

- **エディター画面**: http://localhost:3001
- **API**: http://localhost:3002
- **Remotion Studio**: http://localhost:3000（別途 `npm start` で起動）

### 機能

| タブ | 説明 |
|------|------|
| Script | セリフの一覧表示・編集・追加・削除 |
| Settings | video-settings.yaml の編集 |

### Script画面

- テーブル形式でセリフを一覧表示
- 行クリックで編集モーダルが開く
- キャラクター・表情はドロップダウンで選択
- Visual（画像/テキスト）、SE（効果音）も設定可能
- 「+ Add Line」で新規セリフ追加

### Settings画面

- フォント、字幕、キャラクター、動画、カラーの設定をフォームで編集
- 保存時に `npm run sync-settings` が自動実行される

### Claude Code連携API

Claude CodeがGUIを経由せずにスクリプトを操作するためのAPIも提供しています：

```bash
# 全メタデータ取得（token節約）
curl http://localhost:3002/api/metadata/all

# スクリプト取得
curl http://localhost:3002/api/script

# スクリプト更新
curl -X PUT http://localhost:3002/api/script/1 \
  -H "Content-Type: application/json" \
  -d '{"text": "新しいセリフなのだ！"}'
```

---

## Claude Codeでの使い方

### 基本の流れ

```
┌──────────────────────────────────────┐
│ 1. 「〇〇の紹介動画を作りたい」        │
│         ↓                           │
│ 2. Claudeがセリフを作成               │
│         ↓                           │
│ 3. 「音声生成して」                   │
│         ↓                           │
│ 4. 「プレビュー見せて」で確認          │
│         ↓                           │
│ 5. 修正があれば指示                   │
│         ↓                           │
│ 6. 「動画出力して」で完成！            │
└──────────────────────────────────────┘
```

### よく使う指示

#### 動画を作る
```
「Homebrewの紹介動画を作りたい」
「Pythonの基礎を説明する動画を作って。初心者向けに」
「このアプリの使い方動画を作りたい」
```

#### セリフを修正する
```
「ID 5のセリフを『〇〇〇』に変更して」
「シーン2のセリフをもっと短くして」
「めたんのセリフをもっと増やして」
「専門用語を減らして」
```

#### 発音を修正する
```
「GitHubをギットハブって発音して」
「英語の発音がおかしいところを全部カタカナにして」
```

#### 生成・出力する
```
「音声を生成して」
「プレビュー見せて」
「動画を出力して」
```

---

## セリフの書き方

### ファイル: `src/data/script.ts`

```typescript
export const scriptData: ScriptLine[] = [
  {
    id: 1,                              // ユニークID（連番）
    character: "zundamon",              // "zundamon" または "metan"
    text: "こんにちは！",                // 音声生成用
    displayText: "Hello!",              // 字幕用（省略可）
    scene: 1,                           // シーン番号
    voiceFile: "01_zundamon.wav",       // 音声ファイル名
    durationInFrames: 100,              // 音声生成後に自動更新
    pauseAfter: 10,                     // セリフ後の間（フレーム数）
    emotion: "happy",                   // 表情（省略可）
  },
];
```

### キャラクターの口調

| キャラクター | 役割 | 語尾 | 性格 |
|-------------|------|------|------|
| ずんだもん | 説明役 | 「〜なのだ！」「〜のだ」 | 元気、明るい |
| めたん | 聞き役 | 「〜わ」「〜ね」「〜かしら？」 | 落ち着いた、質問上手 |

---

## 英語の発音問題

VOICEVOXは英語を正しく発音できません。`text`にカタカナ、`displayText`に英語を設定します。

```typescript
{
  text: "ホームブルーでインストールするのだ！",      // 音声用
  displayText: "Homebrewでインストールするのだ！", // 字幕用
}
```

### よく使う変換表

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

## キャラクター画像

### フォルダ構造

```
public/images/
├── zundamon/
│   ├── mouth_open.png      # 通常・口開き（必須）
│   ├── mouth_close.png     # 通常・口閉じ（必須）
│   ├── happy_open.png      # happy表情（任意）
│   ├── happy_close.png     # （任意）
│   └── ...
└── metan/
    └── （同様）
```

**注意:** 表情差分は任意です。`npm run sync-settings`で画像フォルダをスキャンし、存在しない表情は自動的に`mouth_open/mouth_close`にフォールバックします。

### 表情の使い方

**基本ルール:**
- 基本は`normal`（口パク）で話す
- 表情差分は**多用しない**、ここぞというところで使用
- リアクションは最低0.5秒（15フレーム）継続させる

**使いどころ:**
| 表情 | 使うタイミング |
|------|----------------|
| `normal` | 通常の説明、会話（デフォルト） |
| `happy` | 嬉しいとき、褒めるとき、ポイント強調 |
| `surprised` | 驚いたとき、意外な事実 |
| `thinking` | 考え込むとき、説明を聞くとき |
| `sad` | 残念なとき、問題点を指摘 |

```typescript
// NG: 表情を多用しすぎ
{ text: "すごいのだ！", emotion: "happy" },
{ text: "便利なのだ！", emotion: "happy" },

// OK: ここぞというところで使う
{ text: "すごいのだ！" },  // normal（省略可）
{ text: "これが一番のポイントなのだ！", emotion: "happy" },  // ← ここぞ
```

### 画像パスの変更

`video-settings.yaml`で設定：

```yaml
character:
  useImages: true               # 画像を使用する
  imagesBasePath: "images"      # public/images/{characterId}/
  # または共有フォルダ
  # imagesBasePath: "/Users/shared/characters"
```

### 画像の入手先

| キャラクター | 入手先 |
|-------------|--------|
| ずんだもん | [公式](https://zunko.jp/con_illust.html)、ニコニ・コモンズ |
| 四国めたん | [公式](https://zunko.jp/con_illust.html)、ニコニ・コモンズ |

※ 各素材の利用規約を必ず確認してください

---

## スタイル設定（video-settings.yaml）

### デフォルト（黒板風デザイン）

```yaml
# フォント設定
font:
  family: "M PLUS Rounded 1c"   # ポップ体
  size: 70
  weight: "900"                 # エクストラボールド
  color: "#ffffff"              # 白文字
  outlineColor: "character"     # キャラクターごとの色

# キャラクター設定
character:
  height: 275
  useImages: true
  imagesBasePath: "images"

# カラー設定（黒板風）
colors:
  background: "#ffffff"
  zundamon: "#228B22"           # フォレストグリーン
  metan: "#FF1493"              # ディープピンク
```

### おすすめフォント

| フォント | 特徴 |
|----------|------|
| M PLUS Rounded 1c | 丸ゴシック、ポップ（デフォルト） |
| Noto Sans JP | 標準的、読みやすい |
| Kosugi Maru | 丸ゴシック、親しみやすい |

---

## 手動での使い方

### コマンド一覧

| コマンド | 説明 |
|---------|------|
| `npm start` | プレビュー（http://localhost:3000） |
| `npm run voices` | 音声生成（VOICEVOX起動必須） |
| `npm run build` | 動画出力（out/video.mp4） |
| `npm run init` | 新規プロジェクト初期化（スクリプトをリセット） |
| `npm run sync-settings` | YAML設定を反映＋画像スキャン |
| `npm run editor` | GUIエディター起動（http://localhost:3001） |
| `npm run editor:install` | GUIエディターの依存関係インストール |

### 手順

1. `src/data/script.ts` を編集
2. `npm run voices` で音声生成
3. `npm start` でプレビュー確認
4. `npm run build` で動画出力

---

## ファイル構成

```
├── video-settings.yaml      # ★ スタイル設定
├── src/
│   ├── data/
│   │   └── script.ts        # ★ セリフデータ
│   ├── components/
│   │   ├── Character.tsx    # キャラクター表示
│   │   ├── Subtitle.tsx     # 字幕
│   │   └── SceneVisuals.tsx # シーン別ビジュアル
│   ├── config.ts            # 基本設定
│   └── Main.tsx             # メインコンポーネント
├── editor/                  # GUIエディター
│   ├── src/                 # フロントエンド（React + Vite）
│   └── server/              # バックエンド（Express）
├── public/
│   ├── images/              # キャラクター画像
│   └── voices/              # 音声ファイル（自動生成）
└── out/
    └── video.mp4            # 出力動画
```

---

## トラブルシューティング

### VOICEVOXに接続できない
```
Error: ECONNREFUSED
```
→ VOICEVOXアプリが起動しているか確認

### 音声と字幕がずれる
→ `npm run voices` を再実行（durationInFramesが自動修正される）

### 英語の発音がおかしい
→ `text`をカタカナに、`displayText`に英語を設定

### キャラクター画像が表示されない
→ `video-settings.yaml`の`useImages: true`を確認
→ 画像パスを確認

### 音声ファイルが見つからない
```
Error: Could not find file: voices/XX_zundamon.wav
```
→ `npm run voices` で音声を生成

---

## コンテンツ表示（画像・テキスト）

### 画像を表示

セリフごとに`visual`フィールドで画像を指定：

```typescript
{
  id: 3,
  character: "zundamon",
  text: "これがインストール画面なのだ！",
  visual: {
    type: "image",
    src: "install-screen.png",  // public/content/内の画像
    animation: "fadeIn",
  },
}
```

### テキストを表示

```typescript
{
  visual: {
    type: "text",
    text: "ポイント1",
    fontSize: 72,
    color: "#ffffff",
    animation: "bounce",
  },
}
```

### アニメーション

| animation | 効果 |
|-----------|------|
| `none` | アニメーションなし |
| `fadeIn` | フェードイン（デフォルト） |
| `slideUp` | 下から上へスライド |
| `slideLeft` | 右から左へスライド |
| `zoomIn` | 拡大しながら表示 |
| `bounce` | 弾むように表示 |

---

## BGM・効果音

### BGM設定

`src/data/script.ts`でBGMを設定：

```typescript
export const bgmConfig: BGMConfig = {
  src: "background.mp3",  // public/bgm/内のファイル
  volume: 0.3,
  loop: true,
};
```

### 効果音

セリフごとに`se`フィールドで効果音を指定：

```typescript
{
  id: 5,
  character: "zundamon",
  text: "ポイントはここなのだ！",
  se: {
    src: "chime.mp3",  // public/se/内のファイル
    volume: 0.8,
  },
}
```

### フォルダ構造

```
public/
├── bgm/           # 背景音楽
├── se/            # 効果音
├── content/       # コンテンツ画像
├── images/        # キャラクター画像
└── voices/        # 音声ファイル（自動生成）
```

---

## Tips

### 二人で「バイバイ」を合わせる

```typescript
{
  id: 44,
  character: "metan",
  text: "バイバイ〜！",
  pauseAfter: 0,  // ← 間を0に
},
{
  id: 45,
  character: "zundamon",
  text: "バイバイなのだ〜！",
  pauseAfter: 60,
},
```

### 解説に必要な素材を指示する

スクリプトにコメントで記載：

```typescript
{
  id: 5,
  text: "こんな感じでインストールするのだ！",
  // <<ターミナルでbrew installを実行しているスクリーンショット>>
},
```

### コンテンツ表示のルール

- コンテンツは**画面全体を使って最大限大きく**表示
- 無駄な余白は作らない
- 字幕とキャラクターはコンテンツの上に重ねて表示

---

## Claude Code Skillの導入

Claude Codeをより効率的に使うために、専用Skillを導入できます：

```bash
mkdir -p ~/.claude/skills/remotion-video
curl -o ~/.claude/skills/remotion-video/SKILL.md \
  https://raw.githubusercontent.com/nyanko3141592/remotion-voicevox-template/master/SKILL.md
```

Skillを入れると：
- 「紹介動画を作りたい」と言うだけで適切なワークフローを案内
- 英語→カタカナ変換、音声生成の手順を熟知した状態で開始
