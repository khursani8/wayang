# Step 2: Plan the promo

Write promo-plan.md into the delivery directory. The plan is the creative contract for steps 3 and 4.

## Create the output directory

    TS=$(date +%Y%m%d-%H%M%S)
    DELIVERY="promo-output/$TS-<tone>"
    mkdir -p "$DELIVERY"

Generate the timestamp once and reuse it for the whole run.

## Structure of promo-plan.md

    # Promo Plan: <target>

    ## What is the target?
    [one sentence]

    ## The angle
    [creative premise]

    ## Rubric answers
    [the eight step-1 answers]

    ## Tone
    Preset: [name]
    Why: [one line]

    ## Storyboard
    1. momo - "Nak buat video promo tanpa editor video?" - card: none - pause 1.0
    2. momo - "Wayang baca satu YAML, keluar video penuh." - card: "SATU YAML" - pause 1.0
    3. ...

Every row ends with pause 1.0. That is the owner rule. Lines without a card carry "card: none".

## Word-ban pre-check (gate)

    grep -inE '(fail|pypi|kontak)' "$DELIVERY/promo-plan.md" && echo BAN-HIT || echo clean

Record the result in the plan file or in inspect-notes.md.

## Gate

promo-plan.md exists, the storyboard is complete, the word-ban pre-check ran clean.
