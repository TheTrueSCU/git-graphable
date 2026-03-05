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
dd60f448e0f91d0cb92ca53886978136d47cc801[dd60f44 - Demo User - 20260304214922]
style dd60f448e0f91d0cb92ca53886978136d47cc801 fill:#FFD700,color:black
d7c3914fb28d3e0ad3eb7aa73ec9f544e3c634a9[d7c3914 - Demo User - 20260304214922]
style d7c3914fb28d3e0ad3eb7aa73ec9f544e3c634a9 fill:#FFD700,color:black
1a21119e078530e00cd18681d4bd1a7142bc98a6[1a21119 - Demo User - 20260304214922]
style 1a21119e078530e00cd18681d4bd1a7142bc98a6 fill:#FFD700,color:black
2b81bbb8d89e0c4dce5b7b24bbb964bd9092a6ee[2b81bbb - Demo User - 20260304214922]
style 2b81bbb8d89e0c4dce5b7b24bbb964bd9092a6ee fill:#FFD700,color:black
e82d06389b79802c665b7667a7fdfe6d824fbb5c[e82d063 - feature/login - Demo User - 20260304214922]
style e82d06389b79802c665b7667a7fdfe6d824fbb5c fill:#FFD700,color:black
78c6b9ca494fad74836dce2df9795d84f6fcaef4[78c6b9c - main - Demo User - 20260304214922]
style 78c6b9ca494fad74836dce2df9795d84f6fcaef4 fill:#FFD700,color:black,stroke:red,stroke-width:4px
dd60f448e0f91d0cb92ca53886978136d47cc801 --> d7c3914fb28d3e0ad3eb7aa73ec9f544e3c634a9
d7c3914fb28d3e0ad3eb7aa73ec9f544e3c634a9 --> 1a21119e078530e00cd18681d4bd1a7142bc98a6
1a21119e078530e00cd18681d4bd1a7142bc98a6 --> 2b81bbb8d89e0c4dce5b7b24bbb964bd9092a6ee
2b81bbb8d89e0c4dce5b7b24bbb964bd9092a6ee --> e82d06389b79802c665b7667a7fdfe6d824fbb5c
2b81bbb8d89e0c4dce5b7b24bbb964bd9092a6ee --> 78c6b9ca494fad74836dce2df9795d84f6fcaef4
e82d06389b79802c665b7667a7fdfe6d824fbb5c --> 78c6b9ca494fad74836dce2df9795d84f6fcaef4
```

---

## 2. Messy Repository (Score: 76%)
Demonstrates common hygiene issues: WIP commits, direct pushes to protected branches, and stale branch tips.

**Command:**
```bash
git-graphable repo-messy --highlight-wip --highlight-direct-pushes --highlight-stale
```

**Hygiene Report:**
- **Overall Score**: 76% (C)
- **Direct Pushes**: -15% (Non-merge commits on `main`)
- **WIP Commits**: -9% (3 commits with `WIP:` in message)

**Output:**
```mermaid
flowchart TD
9233d74a1bfcd9cbbd2d3e2b91bcfd5154b978b9[9233d74 - Demo User - 20260304214922]
a14287c24abd63537ef54e7551dcfcbd5d0e0c04[a14287c - Demo User - 20260304214922]
14dffb83f2b571280d39b743f274675e2b2bfba5[14dffb8 [DIRECT] - main - Demo User - 20260304214922]
style 14dffb83f2b571280d39b743f274675e2b2bfba5 fill:#fffefe,color:white,stroke:#ff0000,stroke-width:8px,stroke-dasharray: 2 2
ddf1b786131079425a0aaeaaf8d77f3c5a6d3b6d[ddf1b78 [WIP] - Demo User - 20260304214922]
style ddf1b786131079425a0aaeaaf8d77f3c5a6d3b6d fill:#ffff00,color:black
5c369dbf4ddaeeac19935e4ea99a14713344a34f[5c369db [WIP] - Demo User - 20260304214922]
style 5c369dbf4ddaeeac19935e4ea99a14713344a34f fill:#ffff00,color:black
930cd6b92ff791c8efe1832df79a01435759137f[930cd6b [WIP] - feature/draft - Demo User - 20260304214922]
style 930cd6b92ff791c8efe1832df79a01435759137f fill:#ffff00,color:black,fill:#fffefe,color:white
6402c1594e078cd7895b10e0bcdd03ce1b8722ad[6402c15 - stale-branch - Demo User - 20260103214922]
style 6402c1594e078cd7895b10e0bcdd03ce1b8722ad fill:#ffaaaa,color:white
9233d74a1bfcd9cbbd2d3e2b91bcfd5154b978b9 --> a14287c24abd63537ef54e7551dcfcbd5d0e0c04
a14287c24abd63537ef54e7551dcfcbd5d0e0c04 --> 14dffb83f2b571280d39b743f274675e2b2bfba5
14dffb83f2b571280d39b743f274675e2b2bfba5 --> ddf1b786131079425a0aaeaaf8d77f3c5a6d3b6d
ddf1b786131079425a0aaeaaf8d77f3c5a6d3b6d --> 5c369dbf4ddaeeac19935e4ea99a14713344a34f
5c369dbf4ddaeeac19935e4ea99a14713344a34f --> 930cd6b92ff791c8efe1832df79a01435759137f
930cd6b92ff791c8efe1832df79a01435759137f --> 6402c1594e078cd7895b10e0bcdd03ce1b8722ad
```

---

## 3. Special Features (Score: 95%)
Demonstrates topological analysis features like orphan/dangling commits and divergence (behind base).

**Command:**
```bash
git-graphable repo-features --highlight-orphans --highlight-diverging-from main
```

**Output:**
```mermaid
flowchart TD
76f5e037901b66a2109dcb1db086bb240c268b64[76f5e03 - detached-work - Demo User - 20260304214923]
61596df914abe63dbefbe5e8faa9a03aab3bbccc[61596df - Demo User - 20260304214923]
da299065cd4924c948f0eccbece9b47c0253f783[da29906 - main - Demo User - 20260304214923]
style da299065cd4924c948f0eccbece9b47c0253f783 stroke:orange,stroke-width:2px,stroke-dasharray: 5 5
d79edb134c774a4dcffadef66b773f005b114098[d79edb1 - feature/diverged - Demo User - 20260304214923]
61596df914abe63dbefbe5e8faa9a03aab3bbccc --> d79edb134c774a4dcffadef66b773f005b114098
61596df914abe63dbefbe5e8faa9a03aab3bbccc --> da299065cd4924c948f0eccbece9b47c0253f783
```
