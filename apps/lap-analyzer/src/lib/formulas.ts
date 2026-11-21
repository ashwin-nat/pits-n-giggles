// What each game formula shows. Keyed by the session's `formula` string as the recorder writes it
// ("F1 Modern", "F1 26", "F2 2021", "Unknown (255)"); anything not listed is treated as F1.
export interface FormulaRules {
  name: string;
  // True when the name already says the season, so the game year is left off the label.
  yearInName: boolean;
  drs: boolean;
  activeAero: boolean;
  overtake: boolean;
}

const F1: FormulaRules = { name: "F1", yearInName: false, drs: true, activeAero: false, overtake: false };
const F1_26: FormulaRules = { name: "F1 26", yearInName: true, drs: false, activeAero: true, overtake: true };
const F2: FormulaRules = { name: "F2", yearInName: false, drs: true, activeAero: false, overtake: false };

const TABLE: Record<string, FormulaRules> = {
  "f1 26": F1_26,
  f2: F2,
  "f2 2021": F2,
  f1: F1,
  "f1 modern": F1,
  "f1 classic": F1,
  "f1 generic": F1,
  "f1 world": F1,
  "f1 elimination": F1,
};

// Unlisted formulas (Supercars, Esports, Beta) get the F1 marks but keep their own name, so they are
// not grouped with F1 in the game lists. "Unknown (n)" is treated as F1, as the backend does.
export function formulaRules(formula: string): FormulaRules {
  const key = formula.trim().toLowerCase();
  const known = TABLE[key];
  if (known !== undefined) {
    return known;
  }
  return key === "" || key.startsWith("unknown") ? F1 : { ...F1, name: formula.trim() };
}
