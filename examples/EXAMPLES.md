# Git Graphable Examples

This page demonstrates the visual output and hygiene analysis of `git-graphable` using generated example repositories.

## 1. Pristine Repository (Score: 100%)
Demonstrates a clean, PR-based workflow with multi-author highlighting and critical branch marking.

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

## 3. Risk Analysis (Bus Factor)
Highlights branches with many commits but only one contributor. This indicates a "Review Risk."

**Command:**
```bash
git-graphable repo-risk-silo --highlight-silos --silo-threshold 20
```

**Output:**
```mermaid
flowchart TD
3ea61173cf4a6c69db17b4c6501039d33a6982b0["3ea6117 - main - Demo User - 20260305105901"]
5efcb8d1f1ebb2795a738df951c5e06203f262b5["5efcb8d - Alice - 20260305105901"]
9195465c812ad54e5665012678f294b2f22d7184["9195465 - Alice - 20260305105901"]
d3a2ea8a3c8ed7409403d836f4280e7df24fe0a3["d3a2ea8 - Alice - 20260305105901"]
cd27397b8f88e090e5269311b26b77b10a61f954["cd27397 - Alice - 20260305105901"]
43458ccb4b4d435f1e726a71c36f4d74dfef3d88["43458cc - Alice - 20260305105901"]
5781a1dcd158780172ef530c7d3c4a5bbfddbb9b["5781a1d - Alice - 20260305105901"]
192391841cd43546840f9a73ca82d590a596f3d1["1923918 - Alice - 20260305105901"]
1123939f9dc7e8ac88c44560cea2854b25b8633a["1123939 - Alice - 20260305105901"]
3bb33732ee23b3c90eb56131d7c18461e635efab["3bb3373 - Alice - 20260305105901"]
92d7b93cd7f52406236dc1a771c18d3101097ac0["92d7b93 - Alice - 20260305105901"]
edc7e0989161e639f69a2e918315070a9b650257["edc7e09 - Alice - 20260305105901"]
aaa8545d80ce1c7f93f0ed635a642d52e537d418["aaa8545 - Alice - 20260305105901"]
44f32db29d6b3a917fe1f0493a78a563d164eccb["44f32db - Alice - 20260305105901"]
fcb262b2e3dce5b6d005cf5a2ee1e9d51a923053["fcb262b - Alice - 20260305105901"]
588cfa14d70f6679bb53588b4bcb8fa49adedb90["588cfa1 - Alice - 20260305105901"]
fc5736cf0a21cba3426fd0853c24f20592b2c925["fc5736c - Alice - 20260305105901"]
a4f8461065731a429ad9ae8c044827329d3083d5["a4f8461 - Alice - 20260305105901"]
543b5e4de434310b1f90817fd89ac19f735adaa8["543b5e4 - Alice - 20260305105901"]
b1fdd9163e15af3eb69105e1337bbe75813f61f7["b1fdd91 - Alice - 20260305105901"]
b1bba43af1237077c8d101b88d5a2e7aafdd3806["b1bba43 - Alice - 20260305105901"]
807f19736e0a1903dc83ec62cdf810bc5c043a1a["807f197 - Alice - 20260305105901"]
30c28e9ac75e9ca65360d6c000e3dd62b0ff48f7["30c28e9 - Alice - 20260305105901"]
f012b1d4971e5d6e9619396f9adbb32d311e0c80["f012b1d - Alice - 20260305105901"]
76310c4489cb4667e1f31e540b40b42c30b70190["76310c4 - Alice - 20260305105901"]
0007580446cab2af471bc90a29dd094175ef5617["0007580 [SILO] - feature/huge-silo - Alice - 20260305105901"]
style 0007580446cab2af471bc90a29dd094175ef5617 stroke:blue,stroke-width:6px
3ea61173cf4a6c69db17b4c6501039d33a6982b0 --> 5efcb8d1f1ebb2795a738df951c5e06203f262b5
5efcb8d1f1ebb2795a738df951c5e06203f262b5 --> 9195465c812ad54e5665012678f294b2f22d7184
9195465c812ad54e5665012678f294b2f22d7184 --> d3a2ea8a3c8ed7409403d836f4280e7df24fe0a3
d3a2ea8a3c8ed7409403d836f4280e7df24fe0a3 --> cd27397b8f88e090e5269311b26b77b10a61f954
cd27397b8f88e090e5269311b26b77b10a61f954 --> 43458ccb4b4d435f1e726a71c36f4d74dfef3d88
43458ccb4b4d435f1e726a71c36f4d74dfef3d88 --> 5781a1dcd158780172ef530c7d3c4a5bbfddbb9b
5781a1dcd158780172ef530c7d3c4a5bbfddbb9b --> 192391841cd43546840f9a73ca82d590a596f3d1
192391841cd43546840f9a73ca82d590a596f3d1 --> 1123939f9dc7e8ac88c44560cea2854b25b8633a
1123939f9dc7e8ac88c44560cea2854b25b8633a --> 3bb33732ee23b3c90eb56131d7c18461e635efab
3bb33732ee23b3c90eb56131d7c18461e635efab --> 92d7b93cd7f52406236dc1a771c18d3101097ac0
92d7b93cd7f52406236dc1a771c18d3101097ac0 --> edc7e0989161e639f69a2e918315070a9b650257
edc7e0989161e639f69a2e918315070a9b650257 --> aaa8545d80ce1c7f93f0ed635a642d52e537d418
aaa8545d80ce1c7f93f0ed635a642d52e537d418 --> 44f32db29d6b3a917fe1f0493a78a563d164eccb
44f32db29d6b3a917fe1f0493a78a563d164eccb --> fcb262b2e3dce5b6d005cf5a2ee1e9d51a923053
fcb262b2e3dce5b6d005cf5a2ee1e9d51a923053 --> 588cfa14d70f6679bb53588b4bcb8fa49adedb90
588cfa14d70f6679bb53588b4bcb8fa49adedb90 --> fc5736cf0a21cba3426fd0853c24f20592b2c925
fc5736cf0a21cba3426fd0853c24f20592b2c925 --> a4f8461065731a429ad9ae8c044827329d3083d5
a4f8461065731a429ad9ae8c044827329d3083d5 --> 543b5e4de434310b1f90817fd89ac19f735adaa8
543b5e4de434310b1f90817fd89ac19f735adaa8 --> b1fdd9163e15af3eb69105e1337bbe75813f61f7
b1fdd9163e15af3eb69105e1337bbe75813f61f7 --> b1bba43af1237077c8d101b88d5a2e7aafdd3806
b1bba43af1237077c8d101b88d5a2e7aafdd3806 --> 807f19736e0a1903dc83ec62cdf810bc5c043a1a
807f19736e0a1903dc83ec62cdf810bc5c043a1a --> 30c28e9ac75e9ca65360d6c000e3dd62b0ff48f7
30c28e9ac75e9ca65360d6c000e3dd62b0ff48f7 --> f012b1d4971e5d6e9619396f9adbb32d311e0c80
f012b1d4971e5d6e9619396f9adbb32d311e0c80 --> 76310c4489cb4667e1f31e540b40b42c30b70190
76310c4489cb4667e1f31e540b40b42c30b70190 --> 0007580446cab2af471bc90a29dd094175ef5617
```

---

## 4. Redundant History
Highlights redundant back-merges.

**Command:**
```bash
git-graphable repo-complex-hygiene --highlight-back-merges
```

**Output:**
```mermaid
flowchart TD
366874227b985955d27323453b9e075f53065692["3668742 - Demo User - 20260305105901"]
89c693c037b2eab4256beab9ead6572e9c9d0f58["89c693c - Demo User - 20260305105901"]
71589446a700af13cb14ee4fea04c4ab1ad0a1e1["7158944 - Demo User - 20260305105901"]
11f210a834080631aeb343dcec09abde01f15e44["11f210a - Demo User - 20260305105901"]
62d326c80963476bf06537d224f66db9f48f30b4["62d326c [BACK-MERGE] - feature/noisy-history - Demo User - 20260305105901"]
style 62d326c80963476bf06537d224f66db9f48f30b4 stroke:orange,stroke-width:4px,stroke-dasharray: 2 2
96f27dee0ae8c3eb5abb9f9b04b4ead750a729ba["96f27de - main - Demo User - 20260305105901"]
99d822031a58c60594158beecfb254695af84db9["99d8220 - Demo User - 20260305105901"]
594597456b51ab193d76035dc5119f70b4cdaa7a["5945974 - feature/to-be-squashed - Demo User - 20260305105901"]
366874227b985955d27323453b9e075f53065692 --> 89c693c037b2eab4256beab9ead6572e9c9d0f58
366874227b985955d27323453b9e075f53065692 --> 71589446a700af13cb14ee4fea04c4ab1ad0a1e1
89c693c037b2eab4256beab9ead6572e9c9d0f58 --> 62d326c80963476bf06537d224f66db9f48f30b4
71589446a700af13cb14ee4fea04c4ab1ad0a1e1 --> 62d326c80963476bf06537d224f66db9f48f30b4
71589446a700af13cb14ee4fea04c4ab1ad0a1e1 --> 96f27dee0ae8c3eb5abb9f9b04b4ead750a729ba
71589446a700af13cb14ee4fea04c4ab1ad0a1e1 --> 11f210a834080631aeb343dcec09abde01f15e44
11f210a834080631aeb343dcec09abde01f15e44 --> 99d822031a58c60594158beecfb254695af84db9
99d822031a58c60594158beecfb254695af84db9 --> 594597456b51ab193d76035dc5119f70b4cdaa7a
```

---

## 5. Issue Status Mismatch
Highlights desyncs between Git and external trackers (Jira, GitHub Issues).

**Command:**
```bash
git-graphable repo-issue-desync --highlight-issue-inconsistencies --issue-pattern "PROJ-[0-9]+" --issue-engine script --issue-script "echo CLOSED"
```

**Output:**
```mermaid
flowchart TD
7e51353dd8ef68e5daeeb87bfe1b8bc7173c61da["7e51353 - main - Demo User - 20260305124405"]
744e2afb97ef2685efb5bd2074fddb8363e01f8b["744e2af [ISSUE-DESYNC] - feature/PROJ-456 - Demo User - 20260305124405"]
7e51353dd8ef68e5daeeb87bfe1b8bc7173c61da --> 744e2afb97ef2685efb5bd2074fddb8363e01f8b
```

---

## 6. Release Inconsistency
Highlights issues marked as "Released" in the tracker but not yet reachable from a Git tag.

**Command:**
```bash
git-graphable repo-release-desync --highlight-release-inconsistencies --issue-pattern "PROJ-[0-9]+" --issue-engine script --issue-script "echo CLOSED"
```

**Output:**
```mermaid
flowchart TD
9e378b94ef30aa28a742a35e810e3ab1df7962a7["9e378b9 - main - Demo User - 20260305130842"]
33eb58c1867a23375351d97e3d720688d7b58d4a["33eb58c - tags: v1.0.0 - Demo User - 20260305130842"]
da82e4fcb1de2cb38054d4f1b308503617669a32["da82e4f [NOT-RELEASED] - main - Demo User - 20260305130842"]
9e378b94ef30aa28a742a35e810e3ab1df7962a7 --> 33eb58c1867a23375351d97e3d720688d7b58d4a
33eb58c1867a23375351d97e3d720688d7b58d4a --> da82e4fcb1de2cb38054d4f1b308503617669a32
```

---

## 7. Collaboration Gap
Highlights when the Git commit author doesn't match the assigned issue owner in the tracker.

**Command:**
```bash
git-graphable repo-collab-gap --highlight-collaboration-gaps --issue-pattern "PROJ-[0-9]+" --issue-engine script --issue-script "echo OPEN,Bob"
```

**Output:**
```mermaid
flowchart TD
2d3352aa7125b38b108e80bfe564906b0d774703["2d3352a - main - Demo User - 20260305134831"]
cfe995cef9235d83039c5391d29ff4e64d7db222["cfe995c [COLLAB-GAP] - feature/PROJ-777 - Alice - 20260305134831"]
2d3352aa7125b38b108e80bfe564906b0d774703 --> cfe995cef9235d83039c5391d29ff4e64d7db222
```

---

## 8. Topological Analysis
Demonstrates features like orphan/dangling commits and divergence.

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

## 9. CI Mode (Gating)
Demonstrates how to use `git-graphable` as a CI gate.

**Command (Fails):**
```bash
git-graphable repo-messy --check --min-score 80 --bare --highlight-wip --highlight-direct-pushes
```

**Output:**
```text
Error: Hygiene score 76% is below required 80%
```

---

## 10. Interactive HTML Viewer
The HTML engine produces a self-contained, interactive visualization with a live-toggle legend.

**Command:**
```bash
git-graphable repo-messy --engine html -o graph.html
```

**Key Features:**
- **Live Legend**: Toggle hygiene overlays (WIP, Direct Push, Divergence) on/off.
- **Color Modes**: Switch between Authors, PR Status, Distance, and Staleness views.
- **Searchable**: Find specific commits by hash or message.
- **Hierarchical Layout**: Powered by Dagre for a clean top-down flow.
- **Details Sidebar**: View full commit metadata upon selection.

