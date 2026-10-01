# Step 1: Inspect the target

Read the target repository until you can answer the rubric. Work from the repo root: README first, then docs, then the code entry points.

## What to read, in priority order

1. **README.md** - project name, one-line description, install line, the claims it makes about itself.
2. **docs/** - the agent manual (AGENTS.md or docs/), the YAML reference, any tutorial. These give you the real workflow words a viewer would type.
3. **Package metadata** (pyproject.toml / package.json) - real entry points and version.
4. **The code entry** - the CLI module or main module. Extract the real subcommands a promo can show.
5. **Examples in the repo** - projects/, examples/, any demo folder. Real output names beat invented ones.
6. **assets/ or branding** - mascots, logos, colors. A promo for Wayang shows Momo and Kiki; a promo for another repo shows its own identity in text cards.

## The 8-question rubric

Answer all eight in writing before step 2. Quote the target's own words where possible.

```
1. What is the target?
   One sentence: what it does, stated the way the README states it.

2. What is the strongest claim?
   The one line from the repo that earns a reaction.

3. What real artifact can the promo show?
   A command, a YAML key, a version number, a count of something real
   (templates, themes, characters). Text cards must show real things.

4. Who speaks in the promo?
   Wayang promos are voiced by Momo and/or Kiki with Revolab voices.
   Which of the two, or the duo?

5. What does the viewer do next?
   The real install or try-it command from the README.

6. What tone fits?
   The preset whose energy matches the repo. State preset and one line why.

7. Where does output go?
   The timestamped delivery directory name for this run.

8. Q3 and Q5 token check.
   Would the artifact and the call-to-action contain any banned token
   (fail, pypi, kontak)? If yes, rephrase with the real words the repo
   uses instead.
```

## Working notes

Keep inspect notes in the delivery directory as `inspect-notes.md`. They are working notes, not a deliverable.
