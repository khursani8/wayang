# Tone reference

Five tones. Each preset fixes four facets: casting, background theme, pacing, script energy. All pacing values respect the owner rule: every line carries `pause_after: 1.0`. A tone changes how many lines you write and how much text each line carries, never the pause.

Voice ids are Revolab voice ids. Verify an id before promising it: `wayang voices --engine revolab` or read `projects/duo-demo/project.yaml` which carries the ids this skill ships with.

---

## santai

**Casting:** Momo solo, position right. Revolab `paan-f695215e` (ms), `ahmad-642668a6` (en).

**Background:** `studio`.

**Pacing:** 7-8 lines. Conversational text, 8-14 words per line. Warm rhythm: hook, three beats, outro. About 40 seconds rendered.

**Script energy:** First person plural, warm, direct. Hook is a simple question that sets up the reveal.

```
Nak buat video untuk projek anda?
```

**Highlight style:** One idea per line. Feature, then what it means for the viewer.

```
Satu YAML jadi video penuh.
```

**Outro style:** Product name, then a light tagline.

```
Wayang. Cerita anda, cara anda.
```

**Text card animations:** `zoomIn` for titles, `bounce` for the outro card.

**When to use:** Default tone. Most repos, most audiences.

---

## sinematik

**Casting:** Momo (right) + Kiki (left) duo. Revolab: momo `paan-f695215e`, kiki `ali-13002bfa`.

**Background:** `night-sky`.

**Pacing:** 6-7 lines. Short declarative sentences, under 10 words. Trailer rhythm: slow hook, reveal, three sharp beats, slam outro. About 40 seconds rendered.

**Script energy:** Epic. Each sentence lands before the next begins. The duo trades lines like a trailer dialogue.

```
Untuk terlalu lama, video itu susah.
```

**Highlight style:** Capabilities stated like powers, one per line.

```
Templat siap sedia. Watak asli. Suara sebenar.
```

**Outro style:** Name slams in on a full-screen text card, then the tagline.

```
WAYANG. Layar menanti anda.
```

**Text card animations:** `zoomIn` on the reveal card, ALL CAPS card for the name slam.

**When to use:** Launches, big claims, anything with natural scale.

---

## lasak

**Casting:** Momo (right) + Kiki (left) duo, rapid fire.

**Background:** `batik`.

**Pacing:** 9-10 lines. Very short text, 4-8 words. One word or one number per beat after the hook. About 45 seconds rendered.

**Script energy:** Fast and loud. Confidence without exclamation marks. Short words, real numbers from the repo.

```
SATU YAML. SATU ARAHAN. SIAP.
```

**Highlight style:** Rapid-fire claims, each one true and checkable.

```
11 latar tema.
5 templat format.
Dua watak asli.
```

**Outro style:** Name slams. Tagline hits. Done.

```
WAYANG. Video dari YAML.
```

**Text card animations:** `zoomIn`, hard and central.

**When to use:** Hype reels, launch announcements, anything with urgency.

---

## kedai-kopi

**Casting:** Kiki solo, position left. Revolab `ali-13002bfa` (ms), `angel-e67ca253` (en).

**Background:** `kraft-paper`.

**Pacing:** 6-7 lines. One thought per line. Long enough to breathe: 8-12 words. About 40 seconds rendered.

**Script energy:** Calm and dry. The joke is that nothing registers as unusual. One observation, then the product.

```
Dulu, membuat video memerlukan pasukan.
```

**Highlight style:** One quiet sentence per line. No excitement.

```
Kini ia satu arahan terminal.
```

**Outro style:** Product name. Nothing else. Long hold.

```
Wayang.
```

**Text card animations:** `slideUp`, slow and steady.

**When to use:** Testimonial-adjacent promos, tools with a story, restraint as the joke.

---

## komersial

**Casting:** Momo solo, position right. Revolab `paan-f695215e` (ms), `ahmad-642668a6` (en).

**Background:** `whiteboard`.

**Pacing:** 7-8 lines. Feature-card structure: name the feature, then one supporting detail. About 40 seconds rendered.

**Script energy:** Feature-benefit, present tense, clean. Corporate but not boring.

```
Wayang. Video generator untuk pembangun.
```

**Highlight style:** Feature card structure.

```
Sari kata dwibahasa. Bahasa Melayu dan Inggeris, automatik.
```

**Outro style:** Call to action.

```
Pasang hari ini. Cerita anda menunggu.
```

**Text card animations:** `slideLeft` for feature cards.

**When to use:** Serious products, B2B targets, anything that wants to be taken seriously as a product.
