# RFLP docs-as-code pipeline: lint -> export -> needs -> render -> sphinx. `make all` is what CI runs.
SYSML        ?= sysml
SYSML2KIT    ?= sysml2kit
TEST_REPORTS ?= test-reports
SPHINXBUILD  ?= sphinx-build
# `make docs STRICT=` reports RFLP rule violations without failing (layer-by-layer work)
STRICT       ?= -W --keep-going
# sysmlv2-cli fork with the sequence-expression fix (keeps every need in @Realizes { need = ("A", "B"); })
SYSML_GIT     = https://github.com/MichaelD-42/sysml-v2-rs
SYSML_REV     = f55ffbaaa1f107cc78bdd3a1f6003205050eb7e9

MODEL    := $(shell find model -name '*.sysml' | sort)
RESULTS  := $(wildcard test-results/*.xml)
GEN      := docs/_generated
# Usages whose internal structure is drawn, by qualified name (e.g. MyLogical::system MyFunctions::operate)
DIAGRAMS := VehicleLogical::vehicle VehicleFunctions::operateVehicle

.PHONY: all tools lint render docs clean
# always regenerated (< 1 s): make cannot see a deleted model or result file, so staleness checks would keep removed elements
.PHONY: build/model.json $(GEN)/results-needs.json
.DELETE_ON_ERROR:

all: lint docs

tools:
	cargo install --locked --git $(SYSML_GIT) --rev $(SYSML_REV) sysmlv2-cli
	pip install -r requirements.txt

lint:
	$(SYSML) check model

build/model.json: $(MODEL)
	@mkdir -p $(@D)
	$(SYSML) export $(MODEL) > $@

$(GEN)/model-needs.json: build/model.json
	$(SYSML2KIT) needs $< $@ $(MODEL)

# test results become needs linked to their STC/ATC via a <property name="verifies" value="..."/>
$(GEN)/results-needs.json: $(RESULTS)
	@mkdir -p $(@D)
	$(if $(RESULTS),$(TEST_REPORTS) build needs --no-config --need-type testresult --link-property verifies=tests -o $@ $(RESULTS),echo '{"current_version": "", "versions": {"": {"needs": {}}}}' > $@)

render: build/model.json
	@mkdir -p $(GEN)
	$(SYSML2KIT) usecases build/model.json $(GEN)
	for d in $(DIAGRAMS); do $(SYSML) diagram --internal $$d model > $(GEN)/$$(echo $$d | sed 's/.*:://').svg || exit 1; done

# two passes: the trace graph needs the complete need set, RST needs included
docs: $(GEN)/model-needs.json $(GEN)/results-needs.json render
	$(SPHINXBUILD) -q -b needs docs build/needs
	$(SYSML2KIT) trace build/needs/needs.json $(GEN)/trace.svg
	$(SPHINXBUILD) $(STRICT) -b html docs docs/_build/html

clean:
	rm -rf build $(GEN) docs/_build
