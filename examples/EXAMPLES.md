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
30498f7aacb0bf541fd8623d6428d4f6e9128456["30498f7 - Demo User - 20260304224145"]
style 30498f7aacb0bf541fd8623d6428d4f6e9128456 fill:#ADD8E6,color:black
c74b67e729ecc5d1f84ec84a0ce66d16ce6b6d70["c74b67e - Alice - 20260304224145"]
style c74b67e729ecc5d1f84ec84a0ce66d16ce6b6d70 fill:#FFD700,color:black
5d74bc9567204508605af3b82cd16d71d1987418["5d74bc9 - Bob - 20260304224145"]
style 5d74bc9567204508605af3b82cd16d71d1987418 fill:#C0C0C0,color:black
b704f37c2772146788d29d9b012dbfd1513fde42["b704f37 - Charlie - 20260304224145"]
style b704f37c2772146788d29d9b012dbfd1513fde42 fill:#CD7F32,color:black
5a801bf1d00d1b231aabe966e0249b8cd86f91f2["5a801bf - feature/login - Alice - 20260304224145"]
style 5a801bf1d00d1b231aabe966e0249b8cd86f91f2 fill:#FFD700,color:black
d5b17fa132f44795e91f695f21d9968b304964b1["d5b17fa - main - Alice - 20260304224145"]
style d5b17fa132f44795e91f695f21d9968b304964b1 fill:#FFD700,color:black,stroke:red,stroke-width:4px
30498f7aacb0bf541fd8623d6428d4f6e9128456 --> c74b67e729ecc5d1f84ec84a0ce66d16ce6b6d70
c74b67e729ecc5d1f84ec84a0ce66d16ce6b6d70 --> 5d74bc9567204508605af3b82cd16d71d1987418
5d74bc9567204508605af3b82cd16d71d1987418 --> b704f37c2772146788d29d9b012dbfd1513fde42
b704f37c2772146788d29d9b012dbfd1513fde42 --> 5a801bf1d00d1b231aabe966e0249b8cd86f91f2
b704f37c2772146788d29d9b012dbfd1513fde42 --> d5b17fa132f44795e91f695f21d9968b304964b1
5a801bf1d00d1b231aabe966e0249b8cd86f91f2 --> d5b17fa132f44795e91f695f21d9968b304964b1
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
5eb4add741527d3a1b8c7ea474325d08016a1928["5eb4add - Demo User - 20260304224145"]
afc4462c8ac70fe26a10bab2adc3e4848936dde1["afc4462 - Demo User - 20260304224145"]
435272eab8732b5eae6b7eb325c6b7b587ca25b3["435272e [DIRECT] - main - Demo User - 20260304224145"]
style 435272eab8732b5eae6b7eb325c6b7b587ca25b3 fill:#fffefe,color:black,stroke:#ff0000,stroke-width:8px,stroke-dasharray: 2 2
0530c14d7998f74f38ac360a2a95d28a87794bc6["0530c14 [WIP] - Demo User - 20260304224145"]
style 0530c14d7998f74f38ac360a2a95d28a87794bc6 fill:#ffff00,color:black
9d2092bbe88d37c9d1af037e2498069c06b9362e["9d2092b [WIP] - Demo User - 20260304224145"]
style 9d2092bbe88d37c9d1af037e2498069c06b9362e fill:#ffff00,color:black
cde568a89b955f7e27b76207720fd3da670c3aff["cde568a [WIP] - feature/draft - Demo User - 20260304224145"]
style cde568a89b955f7e27b76207720fd3da670c3aff fill:#ffff00,color:black,fill:#fffefe,color:black
524e401cfde4347afed69f4c7f8f8292dbb186b1["524e401 - stale-branch - Demo User - 20260103224145"]
style 524e401cfde4347afed69f4c7f8f8292dbb186b1 fill:#ffaaaa,color:black
5eb4add741527d3a1b8c7ea474325d08016a1928 --> afc4462c8ac70fe26a10bab2adc3e4848936dde1
afc4462c8ac70fe26a10bab2adc3e4848936dde1 --> 435272eab8732b5eae6b7eb325c6b7b587ca25b3
435272eab8732b5eae6b7eb325c6b7b587ca25b3 --> 0530c14d7998f74f38ac360a2a95d28a87794bc6
0530c14d7998f74f38ac360a2a95d28a87794bc6 --> 9d2092bbe88d37c9d1af037e2498069c06b9362e
9d2092bbe88d37c9d1af037e2498069c06b9362e --> cde568a89b955f7e27b76207720fd3da670c3aff
cde568a89b955f7e27b76207720fd3da670c3aff --> 524e401cfde4347afed69f4c7f8f8292dbb186b1
```

---

## 3. Special Features (Score: 93%)
Demonstrates topological analysis features like orphan/dangling commits and divergence (behind base).

**Command:**
```bash
git-graphable repo-features --highlight-orphans --highlight-diverging-from main
```

**Output:**
```mermaid
flowchart TD
f13cad197c59e702b286b4db1898e9c92549f7d5["f13cad1 - Demo User - 20260304224145"]
6d585f8772a0e717d0432a6d18b196322f6a2e62["6d585f8 - tags: v0.0.1-exp - Demo User - 20260304224145"]
style 6d585f8772a0e717d0432a6d18b196322f6a2e62 stroke:#666,stroke-width:2px,stroke-dasharray: 3 3
4df32fa87e669d5cff555af8445a2915d17c1e41["4df32fa - feature/diverged - Demo User - 20260304224145"]
74cf205b9a4c793d464507ddc481ed9bf79051d0["74cf205 - main - Demo User - 20260304224145"]
style 74cf205b9a4c793d464507ddc481ed9bf79051d0 stroke:orange,stroke-width:2px,stroke-dasharray: 5 5
f13cad197c59e702b286b4db1898e9c92549f7d5 --> 4df32fa87e669d5cff555af8445a2915d17c1e41
f13cad197c59e702b286b4db1898e9c92549f7d5 --> 74cf205b9a4c793d464507ddc481ed9bf79051d0
```
