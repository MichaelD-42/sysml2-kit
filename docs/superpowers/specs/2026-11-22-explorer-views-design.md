# Explorer: per-element diagrams and a simpler layout

## Why

The explorer offers every diagram type for every element (`ALWAYS` in `render.js` adds product, compliance, V-model and meta-model to each element's own views), and most of those ignore the focus. The layout splits an 800×600 pane into three columns with nine tabs, inspector, breadcrumb, zoom bar and note above a thumbnail canvas. Michael finds it overwhelming and the diagram choice unhelpful. Goal: picking an element shows one or two diagrams about that element, plus the big-picture diagrams cut down to the element's reach; the page is easy to take in. The meta-model stays, reachable from the header, because it is used to discuss the method with colleagues.

Non-goals: the platform method change (RFQ-owned logical components realized fully, partly or not by platform solutions; supplier use cases from the platform) is a separate project after this one. No change to the model, the bridge or the examples here.

## Views per element

| Selected | This element | In context (scoped) |
|---|---|---|
| CRS / PRQ | Traceability | V-model on its chain, Compliance on its row |
| Use case | Use cases | V-model on the CRS it realizes |
| Feature, function | Traceability | Interfaces of the components its functions are allocated to |
| Logical component | Context, Allocation | Interfaces, V-model on what it satisfies |
| Physical component | Composition, Variants (only for a variation or a part that selects one) | Interfaces, V-model on what reaches it |
| Port | Interfaces of its owner | none |
| System requirement, constraint, test | Traceability | V-model on its chain |

New views and scoping:

- **No activity diagrams** (dropped 2026-11-22): a UML activity refining a use case needs the scenario modelled in the use case (start, decide, fork/join, done; the exporter supports them); the earlier feature activity was composition-like. Revisit with that method change.
- **Allocation** (logical component, new kind `allocation`): the functions allocated to it on the left, the component in the middle, the physical parts it is allocated to on the right, with the requirements it satisfies.
- **Interfaces for a feature or function**: the components its leaf functions are allocated to, with their ports and the connections among them.
- **V-model scoped to any element**: the V narrowed to the element's chain (generalising today's CRS-only `V_REACH`); the whole V stays in the header menu.
- **Compliance scoped to a CRS**: its row only (the full table stays in the header menu).

Model-wide views (Product overview, Compliance, V-model, Meta-model) leave the per-element tabs and go into a header menu labelled **System Model**. Choosing one shows it without a focus; picking an element afterwards returns to that element's tabs.

## Layout

```
┌ Model explorer      [System Model ▾]  [Ask / Search]  Back  Rebuild  Theme ┐
├──────────────┬───────────────────────────────────────────────────────────┤
│ Tree         │ OEM_SeatSwitch «part» LC-100     SeatSwitchRfqLogical /   │
│ (collapsible)│ This element: [Context] [Allocation]                      │
│              │ In context:   [Interfaces] [V-model]                      │
│              │                   diagram, full height                    │
│              │                                                 − Fit +   │
│              │ ▸ Details (doc, requirement links)                        │
└──────────────┴───────────────────────────────────────────────────────────┘
```

- Two columns: tree (collapsible) and diagram. Ask/Search become a panel sliding over the diagram from a header button.
- One title line (name, kind, id, breadcrumb); doc and requirement links in a collapsed Details strip below the canvas.
- Tabs in two labelled groups; only the element's views.
- Zoom floats on the canvas; the domain legend and notes appear only on views that use them.

## Approaches

1. Element views decided client-side from `kind`/`layer` (today's `viewsFor`), server adds the new kinds and a `scope` for V-model and compliance. Chosen: smallest change, keeps the existing split.
2. Server returns the applicable views per element. Rejected: moves UI policy to the server for no gain.

## Left to the builder

Query details, exact empty-state texts, CSS. Keep existing tests passing; add view tests for `allocation`, scoped V-model and scoped compliance, and JS tests for the tab mapping.
