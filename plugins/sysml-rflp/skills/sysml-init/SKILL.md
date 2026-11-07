---
name: sysml-init
description: Scaffold a SysML v2 + sphinx-needs RFLP project (Makefile, model/trace.sysml, Sphinx config with need types, link types and RFLP rules) and install its tools. Use when the user wants to start a new SysML/RFLP project or add the pipeline to an existing repository.
---

# Initialize a project

1. Pick the target directory (default: current). Refuse to overwrite existing files; list conflicts and ask.
2. Copy the template: `cp -rn "${CLAUDE_PLUGIN_ROOT}/templates/project/." <target>/`.
3. Set `project` in `docs/conf.py` to the system name. Create the layer files from `rflp-method` → `references/structure.md` (model layout) with system-prefixed package names, e.g. `package CoolerUseCases { private import Trace::*; }`.
4. Add `docs/customer/requirements.rst` with the customer requirements (`.. crs::` with `:id: CRS-001`), and add it to the toctree in `docs/index.rst`.
5. Tools: `make tools` installs the `sysml` CLI (cargo, from the main branch of the fork in the Makefile) and the Python requirements. Needs Rust and Python 3.10+.
6. Run `make all`. With customer requirements and no model yet, the RFLP rules fail on `crs-satisfied` and `crs-verified`; that is expected and is the starting point for the `rflp` skill.

CI: any runner with Rust and Python runs `make tools && make all`; cache `~/.cargo/bin/sysml` keyed on the commit `git ls-remote <fork> refs/heads/main` reports, so a new commit on the fork rebuilds it.
