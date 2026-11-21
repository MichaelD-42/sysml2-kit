# Interview questions per layer

Ask only what the inputs (CRS, platform, RFQ documents) leave open. One topic at a time. Quote the source when you take a fact from a document. Record each answer as model content, or as an open question when the user does not know yet.

## R: problem space

- Problem statement: what is the customer trying to achieve with the product? One sentence the user would sign.
- Stakeholders: who uses, buys, operates, maintains, certifies it? Each becomes an actor or a source of requirements.
- System boundary and context: what is inside the delivery, what is the customer's or another supplier's? What does it sit in or connect to?
- External interfaces: what crosses the boundary (power, data, mounting, people)? With which standard or part number?
- Operating conditions: environment, duty cycle, lifetime, safety or regulatory class.
- Requirement class: for each CRS, is it functional, non-functional, a constraint or information only? Plain values (mass, speed, voltage) become `CON-` constraints in the model.
- Customer test requirements: which tests does the customer prescribe (CTR), which CRS does each apply to, and can the supplier run them as written or only in part?
- Quantities without values: for each CRS that says "fast", "enough", "long" or names no number, ask for the value and the unit, or mark it open.
- Commercial requirements: warranty, price, delivery, quantity, certification, process. Which of them does the supplier comply with, only in part, or not? Each needs a compliance statement (CST) with that answer.

## F: features and functions

- Which platform features does the customer's need map to? Show the candidates; ask which fit as they are.
- Variant choices: where the platform offers variants (power rating, sensor type), which one does the customer need, or is it still open?
- Which needs have no platform feature? Name them as new features and ask for their functions only where the CRS do not imply them.
- Does a platform feature meet a CRS only in part? State the gap (value not reached, condition excluded); it becomes `partial = true` and an SR.

## L: logical architecture

- What roles does the solution need beyond the platform's own? Ask only for roles the functions cannot be allocated to yet.
- Which interfaces connect the logical components, and what flows through each?
- Are there design constraints that fix a choice (a given supplier, a mandated technology)? Record as an SR or a constraint; do not pick technology here.

## P: physical architecture

- Which platform parts does each logical component map to; which are modified, which are new?
- For each new part: engineering domain (mechanical, electrical, software), and the BOM item, drawing or code module it will be.
- For software parts: which software requirements apply, and where is the code?
- Which physical interfaces (connector, flange, bus message) realize each logical interface?
