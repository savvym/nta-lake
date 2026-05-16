---
change_id: harness-bootstrap-20260516
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: claude-agent:stage6-reviewer
reviewed_at: 2026-05-16T20:06:45Z
verdict: APPROVED
---

# Test Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` artifact 模式。针对"纯文档 + shell 自检"路径做了适配。

- [x] 每条 spec AC 在映射表中至少出现一次（12/12，逐条核对见 §A）。
- [x] 没有 `assert True` 类静态空跑。但部分断言对**内容修改不敏感**（grep OR alternation），见 SHOULD FIX #1。
- [x] Mock 范围声明 = 无；与 unit-test-write SKILL §1.7 "数据访问层禁 mock"在精神上一致（直接读真实文件系统）。
- [x] 测试函数名 `ac1..ac12` 配合 `run_ac` 的显示描述列足够反映 AC 内容，不构成 SKILL §反模式中的 `test_1` / `test_ok`。
- [x] 已知 flaky / 跳过段诚实（无 flaky、无 skip），但**遗漏**了与 AC-2 同类的 OR alternation 脆弱点，见 SHOULD FIX #1。

实际复跑：在 `/data/home/zhhdzhang/nta/nta-lake` 与 `/tmp` 两个 cwd 下分别 `bash <script>` → 都 12/12 PASS、exit 0。故意 `mv .harness/skills/ci-generate/SKILL.md.bak` 后 AC-5 正常 FAIL；在 `wiki/` 放一个 1 行 md 后 AC-11 正常 FAIL；脚本失败路径可达。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | check_harness.sh:51-52 / :88-90 / :105-108（AC-2 / AC-8 / AC-10） | grep alternation 是 OR 关系——文件里只要命中**任一**关键词即 PASS。实证：把 ci-generate/SKILL.md 中 `## 质量门禁` 和 `## 失败回退` 都改名后，AC-10 仍 PASS（剩 `进入条件` 一处命中即过）。AC-2 同 spec review v1 NICE 已记录；AC-8 / AC-10 同类脆弱点 test_report §已知未解决问题未自陈。 | 短期：把 test_report §已知问题段补齐 AC-8 / AC-10 同类 OR 弱点，与 summary §Deferred 的 `harness-tighten-ac-grep-<yyyymmdd>` 对齐。长期：在该 follow-up 中把 `\|` 改成顺序串联 `grep -q A && grep -q B && grep -q C`。 |
| 2 | check_harness.sh:72（AC-5） | 期望值 `[ "$n" -eq 9 ]` 硬编码 9。**未来新增第 10 个 Skill 时此断言会 FAIL**——但 spec AC-5 文字也是"9 个"，所以并非脚本 bug，而是 spec/脚本一同与未来演进耦合。test_report 未提示这一脆弱点。 | 在 test_report §已知未解决问题中补一条："Skills 数量演进时需同步改 spec AC-5 + 本脚本第 72 行 + skills/README.md"；或在 `harness-tighten-ac-grep-*` follow-up 中改成 `[ "$n" -ge 9 ]` 配合白名单。 |
| 3 | check_harness.sh:79（AC-6） | `find _template -type f | wc -l ≥ 10` 只数文件数量，对**文件被清空内容**完全不敏感（实证：_template/ 当前 12 个文件、0 个空文件，但即便把所有 .md 截断到 0 字节，AC-6 仍 PASS）。test_report §已知问题第 3 条已自陈，标注 follow-up `harness-tighten-ac-grep-*`，状态合理。 | 已 deferred，**接受现状**，本条仅为提请评审注意：deferred 链条与 AC-2 NICE 共用同一个 follow-up 变更，确保收口。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | check_harness.sh:21 / 全脚本 | `set -u` 已开，但未开 `set -e` / `set -o pipefail`。当前 `run_ac` 用显式 `if "$@"` 捕获返回码，所以缺 `-e` 不会吞错；但若后续脚本扩展加裸命令，缺 pipefail 容易在 `find ... \| wc -l` 中吞掉左侧失败。 | 不阻塞。后续 follow-up 产品化到 `scripts/check_harness.sh` 时一并加 `set -eo pipefail`，并对 `run_ac` 做局部豁免。 |
| 2 | check_harness.sh:36 | `"$@" >/dev/null 2>&1` 把所有 AC 函数的 stderr 也吞了——失败时排障要靠人手再单独跑 `bash -x ac10` 才看得到具体哪个 SKILL.md 不过。 | 不阻塞。可加一个 `VERBOSE=1` 环境变量分支，或在 FAIL 分支重跑一次不重定向 stderr 打日志。 |
| 3 | test_report_v1.md:73 | "可移植性验证"声称在 `/tmp` 用绝对路径跑了一次 → 已复核通过；但未声明 `bash` 版本要求（`local`、`BASH_SOURCE`、数组 `FAILED_ACS+=()` 都是 bash 特性，alpine busybox /bin/sh 不行）。 | 在 test_report §偏离 SKILL 段或 README 注 "需要 bash ≥ 3.2；busybox/dash 不兼容"。 |
| 4 | test_report_v1.md §偏离 #3 | "测试位置在 change 内 vs `apps/api/tests/`" 引用了"engineering-structure.md 中的 apps/* 当前不存在"作为理由，但**未显式引用** Stage 4 review 末用户选定 B 路径的决策。 | 加一句反向引用 summary.md §关键决策表中的对应行，使 trade-off 的背书链可被回查。 |

## 抽查记录（AC 实质等价性）

| AC | spec 文字 | 脚本断言 | 等价判定 |
|---|---|---|---|
| AC-2 | Owner Agent 含 Rules/Skills/Wiki/MCP 配置索引 + 十阶段调度 + 硬性约束 | grep OR 三关键词命中任一即过 | **断言不足**（OR 弱点，见 SHOULD FIX #1）；但文件实际三段齐全 |
| AC-4 | 每阶段含 Entry / Skill Injection / Quality Gate / Rollback 四要素 | 仅数 `## 阶段 N` 标题 ≥ 10 | **断言不足**——只校验阶段数，未校验四要素齐全。但 spec 验证方式本身就是 `grep -cE` ≥ 10，脚本忠实于 spec，归责在 spec 层，不在本 stage 5 |
| AC-9 | wiki 四份文件 + 8 个核心术语（spec 列：Repository/Layer/Asset/Source Adapter/Processor/Lineage/Commit/Blob） | 脚本 :97 实际只检查 7 个术语，**漏了 `Layer`** | **实质偏差**——spec 写 8 个术语，脚本只检 7 个。但 spec §验收标准表 AC-9 也只写了 7 个（Layer 缺）——脚本与 spec 一致，归责在 spec 层。test_report 应当在 §已知未解决问题中指出这一 spec 内部不一致 |
| AC-12 | `MEMORY.md` + 三份记忆文件 | `test -f` 四份；sed 转义 `pwd \| sed 's\|/\|-\|g'` 验证已实地命中 `-data-home-zhhdzhang-nta-nta-lake` 路径 | 等价；GNU/BSD sed 行为都接受 `s|/|-|g` |

> 上表中 AC-9 的"7 vs 8 术语"是 spec §背景与 §验收表的内部不一致（spec §AC-9 文字列 8 个，spec §验收标准表只列 7 个），脚本忠实于表，不算 stage 5 错。但 test_report 漏报，并入 SHOULD FIX #1 一并补 §已知问题。

## Verdict

**APPROVED**

判据：MUST FIX = 0。SHOULD FIX 3 条均已有 follow-up 跟进位置或仅要求补 test_report 自陈段，不阻塞 Stage 6 通过。NICE TO HAVE 4 条均为长期 hardening，留给 `harness-script-productize-*` / `harness-tighten-ac-grep-*` follow-up。

## 复检指引

Generator 修完（或确认 deferred）后自查：

1. `bash .harness/changes/harness-bootstrap-20260516/unit_test/check_harness.sh` → exit 0 且 12/12 PASS。
2. `cd /tmp && bash <绝对路径>/check_harness.sh` → 同样 12/12 PASS（验证 cwd 无关性）。
3. 故意 `mv .harness/skills/<任一>/SKILL.md SKILL.md.bak`，再跑 → AC-5 必须 FAIL、exit 非 0；恢复后再跑必须回到 12/12。
4. 在 wiki/ 放一个 1 行 md，再跑 → AC-11 必须 FAIL；恢复后回到 12/12。
5. test_report v2 §已知未解决问题：是否补齐 AC-8 / AC-10 OR alternation 弱点 + AC-5 硬编码 9 + AC-9 spec 内部 7 vs 8 术语不一致这 3 条？是否反向链接 summary §关键决策对应 B 路径决策？
6. （若做了）开 `harness-tighten-ac-grep-<yyyymmdd>` follow-up：把 AC-2 / AC-8 / AC-10 OR alternation 改为 AND 串联；同步更新 spec §验收标准表。
7. v2 review 开 `test_review_v2.md`，不覆盖本文件。
