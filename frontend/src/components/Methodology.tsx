import type { ReactNode } from "react";
import { Caption } from "../presenter";
import type { Presets } from "../types";
import { Disclaimer } from "./ui";

const GLOSSARY: [string, string][] = [
  ["Ashby index", "A single number that says how well a material does one job per unit weight, for example the lightest beam that is stiff enough. Named after the materials scientist Michael Ashby; indices follow from the part's load case."],
  ["Density (rho)", "Mass per volume. Lower density means a lighter part."],
  ["Young's modulus (E)", "Stiffness: how strongly the material resists bending or stretching. Measured in GPa."],
  ["Tensile strength (sigma)", "The pulling stress at which the material fails, in MPa."],
  ["Specific stiffness / strength", "Stiffness or strength divided by weight. What matters on an aircraft."],
  ["Hard constraint", "A limit a material must meet to be considered at all, such as a maximum density."],
  ["TOPSIS", "A ranking method that scores each material by how close it is to an imaginary best option and how far from an imaginary worst option."],
  ["Weighted sum", "A ranking method that rescales each factor to 0–1, multiplies by its weight and adds up."],
  ["Weight", "How much a factor matters to you. Weights are rescaled so they add up to 100%."],
  ["Monte Carlo", "Repeating a calculation thousands of times with randomly varied inputs to see how much the answer changes."],
  ["Dirichlet distribution", "A way to randomly vary a set of weights so that they still add up to 100%, centred on the weights you chose."],
  ["Robustness", "How well the recommendation survives changes in priorities and uncertainty in the data."],
  ["Embodied energy", "Energy needed to produce a kilogram of the material, used here as a stand-in for environmental footprint."],
  ["Quasi-isotropic laminate", "A composite layup with fibres in several directions so it is about equally stiff in every in-plane direction."],
  ["Pareto front", "The set of options for which no other option is better on every factor."],
];

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="panel">
      <h2 className="panel-title">{title}</h2>
      <div className="prose-sm mt-2 space-y-2 text-sm leading-relaxed text-slate-800">{children}</div>
    </section>
  );
}

const F = ({ children }: { children: ReactNode }) => <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[13px]">{children}</code>;

export function Methodology({ presets }: { presets: Presets }) {
  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h2 className="text-lg font-bold text-navy-800">Methodology</h2>
      <Caption>How the tool turns a part description into a ranked, confidence-rated list of materials.</Caption>

      <Section title="The idea in one minute">
        <p>
          Choosing a drone material is a trade-off: carbon fibre is stiff and light but costly and hard to recycle, PLA is cheap and printable but softens in the sun, foam survives crashes but carries no load.
          AirframeSelect does five things, in order:
        </p>
        <ol className="list-decimal space-y-1 pl-6">
          <li><strong>Describe the job.</strong> Each part has a load case that decides which Ashby performance index applies.</li>
          <li><strong>Remove what cannot work</strong> using hard limits such as density, strength, temperature, cost and process.</li>
          <li><strong>Score what is left</strong> on six factors with two transparent methods (TOPSIS and weighted sum).</li>
          <li><strong>Test the answer</strong> by re-running it 2000 times with nudged weights and data drawn from each property's range.</li>
          <li><strong>Explain it</strong> with per-factor contributions and a plain-English sentence.</li>
        </ol>
        <p>
          To our knowledge, this combination (part-specific Ashby indices, two transparent ranking methods, Monte Carlo confidence, explanations and printing/sustainability lenses) in a free, open-source UAV-specific tool is uncommon; we make no claim that no other tool does it.
        </p>
      </Section>

      <Section title="1. Ashby performance indices">
        <p>An Ashby index combines properties so that a higher number always means a lighter part for the same job. Density is in Mg/m³, stiffness E in GPa, strength σ in MPa.</p>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[30rem] text-left text-sm">
            <thead><tr className="border-b text-xs uppercase text-slate-500"><th scope="col" className="py-1">Index</th><th scope="col">Formula</th><th scope="col">Meaning</th></tr></thead>
            <tbody>
              {Object.entries(presets.indices).map(([id, i]) => (
                <tr key={id} className="border-b border-slate-100 align-top"><td className="py-1.5 pr-3 font-semibold">{i.label}</td><td className="pr-3"><F>{i.formula}</F></td><td className="text-slate-700">{i.plain}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <p>Values use each property's midpoint; the minimum and maximum of the index are propagated with interval arithmetic (lowest property with highest density, and vice versa) to give the range shown in the Ashby chart and exports.</p>
        <p>On a log–log chart of the index property against density, materials with an equal index lie on a straight line of slope 1/a, where a is the exponent on the property (for example slope 2 for <F>E^(1/2)/ρ</F>). That is the dashed guide line.</p>
        <p><strong>Parts and their indices:</strong> {presets.parts.map((p) => `${p.name} → ${presets.indices[p.performance_index].label}`).join("; ")}.</p>
      </Section>

      <Section title="2. Hard-constraint filter">
        <p>A material is removed if its midpoint density is above the maximum, its strength or service temperature is below the minimum, its cost is above the maximum, or it cannot be made by the required process (or by any process the part allows). Every removed material gets a plain-language reason. The feasible set is then fixed, including in the Monte Carlo step.</p>
      </Section>

      <Section title="3. Six decision criteria">
        <ul className="list-disc space-y-1 pl-6">
          {presets.criteria.map((c) => (
            <li key={c.key}><strong>{c.label}</strong> ({c.direction === "benefit" ? "higher is better" : "lower is better"}): {c.plain}</li>
          ))}
        </ul>
        <p>Impact resistance and recyclability are integer scores from 1 to 5 based on general engineering judgement; the other four come from the data ranges.</p>
      </Section>

      <Section title="4. Ranking methods">
        <p><strong>Weights.</strong> Each part has default weights. A mission profile multiplies them by documented factors ({presets.profiles.map((p) => p.name).join(", ")}) and the result is rescaled to sum to 1. Moving the sliders replaces these weights; rankings depend only on the proportions.</p>
        <p><strong>TOPSIS</strong> (vector normalisation):</p>
        <ol className="list-decimal space-y-1 pl-6">
          <li>Normalise each column: <F>r_ij = x_ij / sqrt(Σ_i x_ij²)</F></li>
          <li>Weight it: <F>v_ij = w_j · r_ij</F></li>
          <li>Ideal best <F>A⁺</F> and worst <F>A⁻</F> take the best and worst value per column (cost columns are reversed).</li>
          <li>Distances: <F>D⁺_i = sqrt(Σ_j (v_ij − A⁺_j)²)</F>, <F>D⁻_i = sqrt(Σ_j (v_ij − A⁻_j)²)</F></li>
          <li>Closeness score: <F>C_i = D⁻_i / (D⁺_i + D⁻_i)</F>, between 0 and 1. Higher is better.</li>
        </ol>
        <p><strong>Weighted sum</strong> (min–max normalisation): benefit criteria <F>n_ij = (x_ij − min_j)/(max_j − min_j)</F>, cost criteria <F>n_ij = (max_j − x_ij)/(max_j − min_j)</F>, score <F>S_i = Σ_j w_j · n_ij</F>. A column in which every material is equal is set to 0.5.</p>
        <p><strong>Agreement.</strong> We report whether the two methods choose the same top 3 and the Spearman rank correlation <F>1 − 6Σd²/(n(n²−1))</F>. When both agree, the answer does not depend on the method you prefer.</p>
        <p>Cost and embodied energy are compared on a plain linear scale, so many cheap materials look alike and only the expensive ones are penalised.</p>
      </Section>

      <Section title="5. Robustness by Monte Carlo">
        <p>By default 2000 seeded trials are run. In each one:</p>
        <ul className="list-disc space-y-1 pl-6">
          <li>weights are drawn from a Dirichlet distribution centred on your weights, with concentration 20 by default (higher = closer to your weights);</li>
          <li>density, stiffness or strength, temperature, cost and embodied energy are drawn uniformly between each material's minimum and maximum, and the Ashby index is recomputed from the draws;</li>
          <li>impact and recyclability scores are held fixed;</li>
          <li>all candidates are re-scored and re-ranked with the chosen method.</li>
        </ul>
        <p>For every material we report the chance of ranking first, the chance of being in the top 3, the median rank, the 5th–95th percentile of its rank and its full rank distribution.</p>
        <p><strong>Confidence label.</strong> The share of trials in which a material lands within 2 places of its baseline rank: <strong>High</strong> at 75% or more, <strong>Medium</strong> at 40% or more, <strong>Low</strong> below that. It describes how stable a position is, not whether the data are correct.</p>
      </Section>

      <Section title="6. Explanations">
        <p>The explainer shows each factor's weighted contribution to a material's score (weight × normalised value). The sentence names the two factors where the material beats the average candidate by the most (weighted by importance) and the one where it falls furthest behind.</p>
      </Section>

      <Section title="7. Data and fairness of comparison">
        <p>Fibre composites use quasi-isotropic or balanced woven laminate values, printed materials use in-plane (XY) values, foams use compressive modulus, and core materials such as honeycomb and aerogel panels use effective values that only apply as a sandwich core. The basis of each record is shown in the Compare view and in the data file.</p>
        <Disclaimer />
      </Section>

      <Section title="8. Limitations">
        <ul className="list-disc space-y-1 pl-6">
          <li>Only typical values are used; no datasheet or test data. All records need spot-checking.</li>
          <li>Ashby indices assume simple beam, panel or tie behaviour; buckling details, joints, fatigue, moisture, vibration and manufacturing quality are not modelled.</li>
          <li>Scores for impact resistance and recyclability are judgement calls, not measurements.</li>
          <li>Uniform sampling inside ranges is a modelling choice, not a measured distribution.</li>
        </ul>
      </Section>

      <Section title="Glossary">
        <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
          {GLOSSARY.map(([t, d]) => (
            <div key={t}><dt className="font-semibold">{t}</dt><dd className="text-slate-700">{d}</dd></div>
          ))}
        </dl>
      </Section>
    </div>
  );
}
