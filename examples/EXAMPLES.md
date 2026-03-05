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
e350703026fb73dc08e890906c9f27547fe52d3d["e350703 - Demo User - 20260304225659"]
style e350703026fb73dc08e890906c9f27547fe52d3d fill:#ADD8E6,color:black
baa77871ec033514ae7cf64b215806d8db52d66e["baa7787 - Alice - 20260304225659"]
style baa77871ec033514ae7cf64b215806d8db52d66e fill:#FFD700,color:black
09389596475bcc38920422347ed068762d994b9a["0938959 - Bob - 20260304225659"]
style 09389596475bcc38920422347ed068762d994b9a fill:#C0C0C0,color:black
e92ac556805176e0bcb22bfbfc9e1c91bb89d40e["e92ac55 - Charlie - 20260304225659"]
style e92ac556805176e0bcb22bfbfc9e1c91bb89d40e fill:#CD7F32,color:black
c4aef5d9923ebf569750358d81bb317b58d6debf["c4aef5d - feature/login - Alice - 20260304225659"]
style c4aef5d9923ebf569750358d81bb317b58d6debf fill:#FFD700,color:black
c00ee886389997fd81c4d7cd66646e14d4b25e23["c00ee88 - main - Alice - 20260304225659"]
style c00ee886389997fd81c4d7cd66646e14d4b25e23 fill:#FFD700,color:black,stroke:red,stroke-width:4px
e350703026fb73dc08e890906c9f27547fe52d3d --> baa77871ec033514ae7cf64b215806d8db52d66e
baa77871ec033514ae7cf64b215806d8db52d66e --> 09389596475bcc38920422347ed068762d994b9a
09389596475bcc38920422347ed068762d994b9a --> e92ac556805176e0bcb22bfbfc9e1c91bb89d40e
e92ac556805176e0bcb22bfbfc9e1c91bb89d40e --> c4aef5d9923ebf569750358d81bb317b58d6debf
e92ac556805176e0bcb22bfbfc9e1c91bb89d40e --> c00ee886389997fd81c4d7cd66646e14d4b25e23
c4aef5d9923ebf569750358d81bb317b58d6debf --> c00ee886389997fd81c4d7cd66646e14d4b25e23
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
0229a6a30e322d32c46f1a6af598a65c3e5e353a["0229a6a - Demo User - 20260304225659"]
6e57a6740ac67d8ce907937159b003dabbdd54f7["6e57a67 - Demo User - 20260304225700"]
0efb5ddfc009cdfde63b43d3cb938b1e5b37fc0d["0efb5dd [DIRECT] - main - Demo User - 20260304225700"]
style 0efb5ddfc009cdfde63b43d3cb938b1e5b37fc0d fill:#fffefe,color:black,stroke:#ff0000,stroke-width:8px,stroke-dasharray: 2 2
f022bb56e83e24629bbe3b2b63cf318a5a552acc["f022bb5 [WIP] - Demo User - 20260304225700"]
style f022bb56e83e24629bbe3b2b63cf318a5a552acc fill:#ffff00,color:black
b9154ef717eefcd4102c339efbf78784d26681a1["b9154ef [WIP] - Demo User - 20260304225700"]
style b9154ef717eefcd4102c339efbf78784d26681a1 fill:#ffff00,color:black
b45e20ac0d914c02cc3bb83af16250d15366f277["b45e20a [WIP] - feature/draft - Demo User - 20260304225700"]
style b45e20ac0d914c02cc3bb83af16250d15366f277 fill:#ffff00,color:black,fill:#fffefe,color:black
6aab5ebb9da86fc58e2b246eda0d04bd7792312d["6aab5eb - stale-branch - Demo User - 20260103225700"]
style 6aab5ebb9da86fc58e2b246eda0d04bd7792312d fill:#ffaaaa,color:black
0229a6a30e322d32c46f1a6af598a65c3e5e353a --> 6e57a6740ac67d8ce907937159b003dabbdd54f7
6e57a6740ac67d8ce907937159b003dabbdd54f7 --> 0efb5ddfc009cdfde63b43d3cb938b1e5b37fc0d
0efb5ddfc009cdfde63b43d3cb938b1e5b37fc0d --> f022bb56e83e24629bbe3b2b63cf318a5a552acc
f022bb56e83e24629bbe3b2b63cf318a5a552acc --> b9154ef717eefcd4102c339efbf78784d26681a1
b9154ef717eefcd4102c339efbf78784d26681a1 --> b45e20ac0d914c02cc3bb83af16250d15366f277
b45e20ac0d914c02cc3bb83af16250d15366f277 --> 6aab5ebb9da86fc58e2b246eda0d04bd7792312d
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
0e186a6c5e12cf892906f609f5e9debee1868f68["0e186a6 - Demo User - 20260304225700"]
ac1456947e4e34408bfe1dcabb0d280284311182["ac14569 - tags: v0.0.1-exp - Demo User - 20260304225700"]
style ac1456947e4e34408bfe1dcabb0d280284311182 stroke:#666,stroke-width:2px,stroke-dasharray: 3 3
6e978d748419ac3151455a37e7cd94d0f2507f84["6e978d7 - feature/diverged - Demo User - 20260304225700"]
style 6e978d748419ac3151455a37e7cd94d0f2507f84 stroke:orange,stroke-width:2px,stroke-dasharray: 5 5
72eb724f8e74e5f67f6f8a6355e820bbbd0daee7["72eb724 - main - Demo User - 20260304225700"]
0e186a6c5e12cf892906f609f5e9debee1868f68 --> 6e978d748419ac3151455a37e7cd94d0f2507f84
0e186a6c5e12cf892906f609f5e9debee1868f68 --> 72eb724f8e74e5f67f6f8a6355e820bbbd0daee7
```
