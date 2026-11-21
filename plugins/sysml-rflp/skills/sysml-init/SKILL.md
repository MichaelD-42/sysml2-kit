---
name: sysml-init
description: Scaffold a SysML v2 + sphinx-needs RFLP project (Makefile, model/trace.sysml, Sphinx config with need types, link types and RFLP rules) and install its tools. Use when the user wants to start a new SysML/RFLP project or add the pipeline to an existing repository.
---

# Initialize a project

1. Pick the target directory (default: current). Refuse to overwrite existing files; list conflicts and ask.
2. Copy the template: `cp -rn "${CLAUDE_PLUGIN_ROOT}/templates/project/." <target>/`.
3. Set `project` in `docs/conf.py` to the system name. Create the layer files from `rflp-method` → `references/structure.md` (model layout) with system-prefixed package names, e.g. `package CoolerUseCases { private import Trace::*; }`; the layer files are requirements, functional (`features.sysml`), logical, physical and verification.
4. Add `docs/customer/requirements.md` with the customer requirements (`:::{crs} Title` with `:id: CRS-001` and `:class: functional|non-functional|constraint|information`, MyST; agree the class with the user), and add it to the toctree in `docs/index.rst`. Commercial ones get `:scope: commercial` and a compliance statement in `docs/customer/statements.md`.
5. If the supplier has a platform repo: `git submodule add <platform repo> platform`. `make` picks up `platform/model/` itself. Skip when there is none.
6. Tools: `make tools` installs the `sysml` CLI (cargo, from the fork tag `SYSML_TAG` in the Makefile) and the Python requirements. Needs Rust and Python 3.10+.
7. Run `make all`. With customer requirements and no model yet, the RFLP rules fail on `crs-satisfied` and the compliance `not verified` finding; that is expected and is the starting point for the `rflp` or `rfq` skill.

CI: any runner with Rust and Python runs `make tools && make all`; cache `~/.cargo/bin/sysml` keyed on `SYSML_TAG`, so changing the tag rebuilds it.
