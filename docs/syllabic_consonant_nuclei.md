# Design note: /l n r/ as fallback nuclei (syllabic sonorants)

Status: **sketch, not implemented.** Today a nucleus must be a vowel or a true
diphthong; a schwa-less reduced syllable has no nucleus and `syllabify` raises
`ValueError`. This note sketches an opt-in fallback that lets a sonorant
`/l n r/` (optionally `/m/`) act as a syllabic nucleus, without becoming greedy.
Reference: Booij (1995), *The Phonology of Dutch*, on syllabic sonorants.

## The phenomenon

In casual/reduced Dutch the schwa of a final unstressed syllable can drop,
leaving a syllabic sonorant:

```
appel   [ɑpəl] ~ [ɑpl̩]     ['ɑ','p','l']
open    [oːpə(n)] ~ [oːpn̩]  ['oː','p','n']
beter   [beːtər] ~ [beːtr̩]  ['beː','t','r']
```

These have one syllable more than their vowel count suggests. With vowels only,
`['ɑ','p','l']` looks like "no nucleus".

## Design goals

1. **Vowels always win.** A sonorant is *only* considered when a stretch has no
   vowel/diphthong nucleus to host it. Never split a sequence that already
   parses with vowel nuclei.
2. **Not greedy.** Promote at most the minimum number of sonorants needed, and
   never a sonorant that sits directly next to a vowel that could host it
   (that sonorant is just a coda/onset consonant).
3. **Opt-in.** Default `allow_syllabic_consonants=False`, so current behavior
   (raise on no-nucleus) is unchanged.

## How it could work

Two-pass, after the existing vowel-nucleus detection:

1. Find true nuclei (vowels + diphthongs) as today.
2. If `allow_syllabic_consonants` and a maximal **vowelless run** remains
   (either the whole word has zero vowel nuclei, or a trailing consonant tail
   cannot be a single legal coda), promote sonorants in that run:
   - eligible phones: `/l n r/` (config-extendable to `/m/`);
   - choose the position where a schwa would have been: scan the run
     **right-to-left**, and promote the *rightmost* eligible sonorant that is
     (a) preceded by a less-sonorous consonant (an obstruent or nasal), and
     (b) not immediately adjacent to an existing vowel nucleus;
   - re-run the maximal-onset split treating the promoted sonorant as a nucleus;
   - if a long vowelless run still strands consonants, repeat for the next
     eligible sonorant leftward (rare in Dutch — usually at most one per word).

### Anti-greed guards

- Require the promoted sonorant to be **more sonorous than its left neighbour**
  (so `/p l/` -> syllabic `l`, but a vowel-adjacent `/aː l/` stays a coda `l`).
- Forbid promotion adjacent to a vowel nucleus on either side.
- Prefer the rightmost candidate; only add a second nucleus if consonants would
  otherwise be unsyllabifiable.
- Keep `/r/` cautious: many varieties keep schwa before `/r/`; consider making
  `/r/` promotion separately toggleable.

## Sketch

```python
SYLLABIC_SONORANTS = ('l', 'n', 'r')   # 'm' optional

def _fallback_nuclei(labels, nuclei, allow):
    '''Indices of sonorants to treat as nuclei, or [] when not needed.'''
    if not allow or nuclei:            # vowels present -> never promote
        return []
    promoted = []
    for i in range(len(labels) - 1, 0, -1):     # right to left
        lab = labels[i]
        if lab in SYLLABIC_SONORANTS and _less_sonorous(labels[i - 1], lab):
            promoted.append(i)
            if _rest_is_legal_coda(labels, i):  # remaining tail is coda-legal
                break
    return sorted(promoted)
```

This keeps the core Maximal-Onset logic intact: fallback nuclei simply extend
the nucleus index list before `_maximal_onset_split` runs.

Recommended scope: start with whole-word **vowelless** inputs only (the clearest
case), `/l n r/`, single promotion, behind the default-off flag. Broaden to
trailing-tail promotion and `/m r/` toggles once the simple case is validated
against real reduced transcriptions.
