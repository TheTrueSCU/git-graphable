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
982f31213e9ecbaf57f6c94b3b08ba57421d0e5d["982f312 - Demo User - 20260304230337"]
style 982f31213e9ecbaf57f6c94b3b08ba57421d0e5d fill:#ADD8E6,color:black
2bed5833e7769dc0bb2d3a555c2a3e5ac176ba5d["2bed583 - Alice - 20260304230337"]
style 2bed5833e7769dc0bb2d3a555c2a3e5ac176ba5d fill:#FFD700,color:black
8fd8bfd7e2cb1c02e3ae4971e1d5ddfec3a4cde2["8fd8bfd - Bob - 20260304230337"]
style 8fd8bfd7e2cb1c02e3ae4971e1d5ddfec3a4cde2 fill:#C0C0C0,color:black
2a76137d56f94f16f5077a0b61082d7f1c878ebc["2a76137 - Charlie - 20260304230337"]
style 2a76137d56f94f16f5077a0b61082d7f1c878ebc fill:#CD7F32,color:black
f134cccd580ff06917b9466378dac92411ea7d16["f134ccc - feature/login - Alice - 20260304230337"]
style f134cccd580ff06917b9466378dac92411ea7d16 fill:#FFD700,color:black
a7927f460a42b06a00c15a29db85d9cc99ddd451["a7927f4 - main - Alice - 20260304230337"]
style a7927f460a42b06a00c15a29db85d9cc99ddd451 fill:#FFD700,color:black,stroke:red,stroke-width:4px
982f31213e9ecbaf57f6c94b3b08ba57421d0e5d --> 2bed5833e7769dc0bb2d3a555c2a3e5ac176ba5d
2bed5833e7769dc0bb2d3a555c2a3e5ac176ba5d --> 8fd8bfd7e2cb1c02e3ae4971e1d5ddfec3a4cde2
8fd8bfd7e2cb1c02e3ae4971e1d5ddfec3a4cde2 --> 2a76137d56f94f16f5077a0b61082d7f1c878ebc
2a76137d56f94f16f5077a0b61082d7f1c878ebc --> f134cccd580ff06917b9466378dac92411ea7d16
2a76137d56f94f16f5077a0b61082d7f1c878ebc --> a7927f460a42b06a00c15a29db85d9cc99ddd451
f134cccd580ff06917b9466378dac92411ea7d16 --> a7927f460a42b06a00c15a29db85d9cc99ddd451
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
f5b0c6426e5abe4b29f1035ef0ed2c0380b42b65["f5b0c64 - Demo User - 20260304230337"]
f534dfb429831e547f418960a9c1091af158664d["f534dfb - Demo User - 20260304230337"]
147f97d5dd2c89f8078e0cc67aab5d495485b67c["147f97d [DIRECT] - main - Demo User - 20260304230337"]
style 147f97d5dd2c89f8078e0cc67aab5d495485b67c fill:#fffefe,color:black,stroke:#ff0000,stroke-width:8px,stroke-dasharray: 2 2
8019681c6043e90161786b53dae5b2931ca672f7["8019681 [WIP] - Demo User - 20260304230337"]
style 8019681c6043e90161786b53dae5b2931ca672f7 fill:#ffff00,color:black
026430e614fe5d40b2083ae18ffc896e6a19f9bd["026430e [WIP] - Demo User - 20260304230337"]
style 026430e614fe5d40b2083ae18ffc896e6a19f9bd fill:#ffff00,color:black
5e8141b4219997ef927be1aa9b239d5b9a13ca7b["5e8141b [WIP] - feature/draft - Demo User - 20260304230337"]
style 5e8141b4219997ef927be1aa9b239d5b9a13ca7b fill:#ffff00,color:black,fill:#fffefe,color:black
f9448431e9272128f0e5a6ebab0b2a77efddbbd1["f944843 - stale-branch - Demo User - 20260103230337"]
style f9448431e9272128f0e5a6ebab0b2a77efddbbd1 fill:#ffaaaa,color:black
f5b0c6426e5abe4b29f1035ef0ed2c0380b42b65 --> f534dfb429831e547f418960a9c1091af158664d
f534dfb429831e547f418960a9c1091af158664d --> 147f97d5dd2c89f8078e0cc67aab5d495485b67c
147f97d5dd2c89f8078e0cc67aab5d495485b67c --> 8019681c6043e90161786b53dae5b2931ca672f7
8019681c6043e90161786b53dae5b2931ca672f7 --> 026430e614fe5d40b2083ae18ffc896e6a19f9bd
026430e614fe5d40b2083ae18ffc896e6a19f9bd --> 5e8141b4219997ef927be1aa9b239d5b9a13ca7b
5e8141b4219997ef927be1aa9b239d5b9a13ca7b --> f9448431e9272128f0e5a6ebab0b2a77efddbbd1
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
5223ed03ff44ab68ffe4985a1d5cfba93a41972a["5223ed0 - Demo User - 20260304230337"]
433d77f339a1d5a9e51ae7d614dce9bb813c0789["433d77f - tags: v0.0.1-exp - Demo User - 20260304222925"]
style 433d77f339a1d5a9e51ae7d614dce9bb813c0789 stroke:#666,stroke-width:2px,stroke-dasharray: 3 3
ebeaa6afb7b85a2d84d8aa5279ca3ad50f54a987["ebeaa6a - feature/diverged - Demo User - 20260304230337"]
style ebeaa6afb7b85a2d84d8aa5279ca3ad50f54a987 stroke:orange,stroke-width:2px,stroke-dasharray: 5 5
6b7150fa345c274de280b021c7c94300b0920604["6b7150f - main - Demo User - 20260304230337"]
5223ed03ff44ab68ffe4985a1d5cfba93a41972a --> ebeaa6afb7b85a2d84d8aa5279ca3ad50f54a987
5223ed03ff44ab68ffe4985a1d5cfba93a41972a --> 6b7150fa345c274de280b021c7c94300b0920604
```

---

## 4. CI Mode (Gating)
Demonstrates how to use `git-graphable` as a CI gate. The tool returns a non-zero exit code if the hygiene score is below the threshold.

**Command (Fails):**
```bash
# repo-messy score is 76%, so this fails
git-graphable repo-messy --check --min-score 80 --bare --highlight-wip --highlight-direct-pushes
```

**Output:**
```text
Error: Hygiene score 76% is below required 80%
```

**Command (Passes):**
```bash
# repo-pristine score is 100%, so this passes
git-graphable repo-pristine --check --min-score 80 --bare
```

**Output:**
```text
Success: Hygiene score 100% meets required 80%
```
