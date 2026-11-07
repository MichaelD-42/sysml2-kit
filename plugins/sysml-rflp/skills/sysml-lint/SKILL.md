---
name: sysml-lint
description: Validate SysML v2 models with `sysml check` in a fix loop, and measure impact before renaming or deleting model elements. Use when lint fails, after .sysml edits, or before a rename/delete.
---

# SysML v2 lint loop

1. `sysml --format json check model` (or `make lint`).
2. `"ok": true` and exit 0: done.
3. Otherwise fix each entry of `parseErrors`, `unresolved` (`path`, `line`, `column`, `didYouMean`), `collisions`, `violations` at its location. Prefer a `didYouMean` candidate over inventing a name.
4. Rerun. Stop after 5 rounds; report what remains with file:line and message.

Do not silence a finding by deleting the referencing element unless the user asked for that.

## Before renaming or deleting

1. `grep -rn "<name or short name>" model docs` finds textual uses, including RST links to the id.
2. Make the change, run `sysml check model`: every `unresolved` entry is a broken use.
3. If an id changed or disappeared, `make all` must still pass; RST links to it and RFLP rules fail otherwise.

## Misleading messages

- A violation about an unrelated construct (`WhileLoopActionUsage`, "Expression must have exactly one ... ResultParameterMembership") usually means a keyword used as a name, or a package name colliding with the standard library (`UseCases`). Rename it.
