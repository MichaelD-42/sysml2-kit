# RFLP docs-as-code pipeline: lint -> export -> needs -> render -> sphinx. `make all` is what CI runs.
SYSML        ?= sysml
SYSML2KIT    ?= sysml2kit
TEST_REPORTS ?= test-reports
SPHINXBUILD  ?= sphinx-build
# `make docs STRICT=` reports RFLP rule violations without failing (layer-by-layer work)
STRICT       ?= -W --keep-going
# sysmlv2-cli fork (sequence-expression fix, variant-id fix, find/relations MCP tools), pinned to a tag so every install gets the same checker
SYSML_GIT     = https://github.com/MichaelD-42/sysml-v2-rs
SYSML_TAG     = v0.2.0-kit.5

MODEL    := $(shell find model -name '*.sysml' | sort)
# make splits file names on spaces, so `my part.sysml` would become two missing files
$(if $(shell find model -name '*.sysml' -name '* *'),$(error model file names must not contain spaces; rename: $(shell find model -name '*.sysml' -name '* *')))
# the platform project: a git submodule at platform/, or the path to its checkout (no symlink: Windows checks one out as a file)
PLATFORM := platform
# the platform's model, without its trace.sysml: a second package Trace
PLATFORM_MODEL := $(shell test -d $(PLATFORM)/model && find $(PLATFORM)/model -name '*.sysml' ! -path $(PLATFORM)/model/trace.sysml | sort)
RESULTS  := $(wildcard test-results/*.xml)
GEN      := docs/_generated
# Usages whose internal structure is drawn, by qualified name (e.g. MyLogical::system MyFunctions::operate)
DIAGRAMS :=

.PHONY: all tools lint render docs clean mcp
# always regenerated (< 1 s): make cannot see a deleted model or result file, so staleness checks would keep removed elements
.PHONY: build/model.json $(GEN)/results-needs.json
.DELETE_ON_ERROR:

all: lint docs

tools:
	cargo install --locked --git $(SYSML_GIT) --tag $(SYSML_TAG) sysmlv2-cli
	pip install -r requirements.txt

lint:
	$(SYSML) check model $(PLATFORM_MODEL)

# the sysml MCP server on the project and its platform, as make sees them; the plugin's .mcp.json runs `make -s mcp`
# (a platform inside the project, the submodule, is read once)
mcp:
	@exec $(SYSML) mcp --project . $(if $(PLATFORM_MODEL),--project $(PLATFORM))

build/model.json: $(MODEL) $(PLATFORM_MODEL)
	@mkdir -p $(@D)
	$(SYSML) export $(MODEL) $(PLATFORM_MODEL) > $@

$(GEN)/model-needs.json: build/model.json
	$(SYSML2KIT) needs $< $@ $(MODEL) $(PLATFORM_MODEL) --platform $(PLATFORM_MODEL)

# test results become needs linked to their STC/ATC via a <property name="verifies" value="..."/>
$(GEN)/results-needs.json: $(RESULTS)
	@mkdir -p $(@D)
	$(if $(RESULTS),$(TEST_REPORTS) build needs --no-config --need-type testresult --link-property verifies=tests -o $@ $(RESULTS),echo '{"current_version": "", "versions": {"": {"needs": {}}}}' > $@)

render: build/model.json
	@mkdir -p $(GEN)
	# start empty: a renamed subject or a dropped DIAGRAMS entry must not leave its old picture behind
	rm -f $(GEN)/*.svg
	$(SYSML2KIT) usecases build/model.json $(GEN)
	@# each diagram is saved under its last name segment, so two entries ending alike would overwrite each other
	@dups=$$(for d in $(DIAGRAMS); do echo $${d##*::}; done | sort | uniq -d); \
	if [ -n "$$dups" ]; then echo "DIAGRAMS: more than one entry ends in $$dups" >&2; exit 1; fi
	for d in $(DIAGRAMS); do $(SYSML) diagram --internal $$d model $(PLATFORM_MODEL) > $(GEN)/$$(echo $$d | sed 's/.*:://').svg || exit 1; done

# two passes: the trace graph and the compliance table need the complete need set, Markdown and RST needs included
docs: $(GEN)/model-needs.json $(GEN)/results-needs.json render
	$(SPHINXBUILD) -q -b needs docs build/needs
	$(SYSML2KIT) trace build/needs/needs.json $(GEN)/trace.svg
	$(SYSML2KIT) compliance build/needs/needs.json $(GEN)/compliance.md $(if $(STRICT),,--warn-only)
	$(SPHINXBUILD) $(STRICT) -b html docs docs/_build/html

clean:
	rm -rf build $(GEN) docs/_build
