# Capturing a platform bottom-up

Use when the project is the platform itself (same layout as an RFQ project, no `platform/` inside it, ids carry the platform tag such as `WSW-`). The workflow runs in reverse: start from what exists and ask upward. PRQ (`prq` directives in `docs/platform/`) play the role CRS play in an RFQ project.

## 1. Physical components from what exists

Inputs: a BOM or parts list, the code repository, layouts, datasheets. For each item that is built or bought, create a PC with `physical-architect` conventions:

- `#Mechanical`, `#Electrical` or `#Software part <'WSW-PC-nnn'> name`, exactly one domain; the `doc` names the BOM item or code module. Mechanical and electrical items come from the BOM, software from the code repository.
- Variants of one part (left- and right-hand housing) are `variation #Mechanical part` with `variant #Mechanical part` members, each with its own id.
- The product as built is an `#Assembly part <'WSW-PC-nnn'>` (no domain) typed by a part definition that states the rated values; the platform's constraints sit on it or its definition. The logical switch is not typed by it.
- Physical interfaces (`port <'WSW-PI-nnn'>`: connector, flange, bus message) where another part attaches.
- Software PCs get `swreq` needs in `docs/software/*.md` (`:allocated_to:` the SW component or unit) and links to code and tests.

Ask the user to confirm the list before going up; do not guess BOM structure from file names alone. Cite the file each PC came from.

## 2. Interview upward

For each PC, one topic at a time:

- Logical role: what does this part do in technology-neutral terms? Group PCs under LCs (`ACME_WindowSwitch` with `keySensing`, `switchController`, `linCommunication`, `enclosure`); `allocate <LC> to <PC>`, and LI to PI.
- Functions: what does each LC do? Verb + noun; nest sub-functions where a function has steps. `allocate` each leaf function to its LC.
- Features: what does the supplier sell? A `#Feature action` per offering with a noun name, owning its functions; one use case per way a vehicle or user uses it, performing the features.
- Variants: which variation parts does the customer choose between, and in which feature does the choice show?
- Requirements: what does the platform promise (PRQ, with values)? Derive SRs from them, `satisfy` them from the LCs, and verify them with STCs.

## 3. Rules

The platform build checks its own chain with the same rules (PRQ as CRS), so run the `rflp` steps' reviews on each layer as you go. The platform never contains RFQ ids, `@Matches` or links to a customer. An RFQ project reaches the platform only through `platform/` and subsetting (`:>`).
