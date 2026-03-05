# Git Graphable Examples

This page demonstrates the visual output and hygiene analysis of `git-graphable` using generated example repositories.

## 1. Pristine Repository (Score: 100%)
Demonstrates a clean, PR-based workflow with author highlighting and critical branch marking.

**Command:**
```bash
git-graphable repo-pristine --highlight-critical --critical-branch main --highlight-authors
```

**Output:**
```mermaid
flowchart TD
bb58b9059c8cb1dda782f006f49d17549dd91c21["bb58b90 - Demo User - 20260304223102"]
style bb58b9059c8cb1dda782f006f49d17549dd91c21 fill:#ADD8E6,color:white
55d625535ebebec378dea6a807f6cf45679c494f["55d6255 - Alice - 20260304223102"]
style 55d625535ebebec378dea6a807f6cf45679c494f fill:#FFD700,color:black
02b5227a82af192724100e9cd30e117ed5836af8["02b5227 - Bob - 20260304223102"]
style 02b5227a82af192724100e9cd30e117ed5836af8 fill:#C0C0C0,color:white
8b47affbfef2f3632d576f0d8def06ef3d21ec3a["8b47aff - Charlie - 20260304223102"]
style 8b47affbfef2f3632d576f0d8def06ef3d21ec3a fill:#CD7F32,color:white
6f627e9d4d9d984612bd7991b2f66ccd25d851e9["6f627e9 - feature/login - Alice - 20260304223102"]
style 6f627e9d4d9d984612bd7991b2f66ccd25d851e9 fill:#FFD700,color:black
94ad06534ef62b223eb6a38b19dd12226e985c68["94ad065 - main - Alice - 20260304223102"]
style 94ad06534ef62b223eb6a38b19dd12226e985c68 fill:#FFD700,color:black,stroke:red,stroke-width:4px
bb58b9059c8cb1dda782f006f49d17549dd91c21 --> 55d625535ebebec378dea6a807f6cf45679c494f
55d625535ebebec378dea6a807f6cf45679c494f --> 02b5227a82af192724100e9cd30e117ed5836af8
02b5227a82af192724100e9cd30e117ed5836af8 --> 8b47affbfef2f3632d576f0d8def06ef3d21ec3a
8b47affbfef2f3632d576f0d8def06ef3d21ec3a --> 6f627e9d4d9d984612bd7991b2f66ccd25d851e9
8b47affbfef2f3632d576f0d8def06ef3d21ec3a --> 94ad06534ef62b223eb6a38b19dd12226e985c68
6f627e9d4d9d984612bd7991b2f66ccd25d851e9 --> 94ad06534ef62b223eb6a38b19dd12226e985c68
```

---

## 2. Messy Repository (Score: 76%)
...
- **WIP Commits**: -9% (3 commits with `WIP:` in message)

**Output:**
```mermaid
flowchart TD
db34c8b2ccd1a3bb3bc59afbcd31b9d5b5480de0["db34c8b - Demo User - 20260304221751"]
b7916dd27ffa9ba4b27a3a8b62a1e01a468d0152["b7916dd - Demo User - 20260304221751"]
cfebaf4d2fd36f57a99b5393bc3a91622f7cb464["cfebaf4 [DIRECT] - main - Demo User - 20260304221751"]
style cfebaf4d2fd36f57a99b5393bc3a91622f7cb464 fill:#fffefe,color:white,stroke:#ff0000,stroke-width:8px,stroke-dasharray: 2 2
e4c893e0fd7da6e2f04ff3979a31e6af0c05e1f2["e4c893e [WIP] - Demo User - 20260304221751"]
style e4c893e0fd7da6e2f04ff3979a31e6af0c05e1f2 fill:#ffff00,color:black
ecd3cd1c4f19c654badf2f790008c996b8fc1560["ecd3cd1 [WIP] - Demo User - 20260304221751"]
style ecd3cd1c4f19c654badf2f790008c996b8fc1560 fill:#ffff00,color:black
204555443feebb5bf0619ce353fd5ea778ae0458["2045554 [WIP] - feature/draft - Demo User - 20260304221751"]
style 204555443feebb5bf0619ce353fd5ea778ae0458 fill:#ffff00,color:black,fill:#fffefe,color:white
5c3d6a8918d480cdc8ea2f48536b2acd58cae4c3["5c3d6a8 - stale-branch - Demo User - 20260103221751"]
style 5c3d6a8918d480cdc8ea2f48536b2acd58cae4c3 fill:#ffaaaa,color:white
db34c8b2ccd1a3bb3bc59afbcd31b9d5b5480de0 --> b7916dd27ffa9ba4b27a3a8b62a1e01a468d0152
b7916dd27ffa9ba4b27a3a8b62a1e01a468d0152 --> cfebaf4d2fd36f57a99b5393bc3a91622f7cb464
cfebaf4d2fd36f57a99b5393bc3a91622f7cb464 --> e4c893e0fd7da6e2f04ff3979a31e6af0c05e1f2
e4c893e0fd7da6e2f04ff3979a31e6af0c05e1f2 --> ecd3cd1c4f19c654badf2f790008c996b8fc1560
ecd3cd1c4f19c654badf2f790008c996b8fc1560 --> 204555443feebb5bf0619ce353fd5ea778ae0458
204555443feebb5bf0619ce353fd5ea778ae0458 --> 5c3d6a8918d480cdc8ea2f48536b2acd58cae4c3
```

---

## 3. Special Features (Score: 93%)
...
```
