#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mining a small subgroup out of a large public database

Single-file distribution of the "niche-data-workflow" skill. Running this script writes a ready-to-use
SKILL.md that can be dropped into a skills directory.

Usage
  python niche_data_workflow.py                 write ./niche-data-workflow/SKILL.md
  python niche_data_workflow.py --dir PATH      write PATH/niche-data-workflow/SKILL.md
  python niche_data_workflow.py --print         print the skill to standard output
  python niche_data_workflow.py --check         verify that the embedded text is complete

No third-party packages are required. Python 3.8 or later.
"""

import argparse
import os
import sys

NAME = "niche-data-workflow"

CONTENT = r"""---
name: niche-data-workflow
description: A workflow for carving a small subgroup out of a large public database and building a defensible study on it. Trigger when the user says "I want to use this database for a narrow question", "there are only sixty observations, can I still do this", "how do I find an angle nobody has taken in a public survey", "this subgroup is too small to infer from", "how should I define the group so it holds up", or "how do I show this is not an artefact", or when they hold a large file and only a vague interest. Applies to national household surveys, administrative claims, registries, hospital discharge data and insurance settlement data. Not for literature review (use ima-report), re-running existing analyses, or primary data collection.
---

# Building a study on a small subgroup

The shape of this work is fixed: **one large public database, one small subgroup, one question nobody has asked**. The difficulty is not statistical. It lies in three judgements: whether the subgroup can be identified at all, how many observations remain once it is identified, and whether what remains can carry the conclusion you want. If any of the three fails, the paper fails.

Being small is not a defect; it is where topics come from. The mainstream population in a big survey has been worked over. The gaps sit in low-prevalence services, excluded indications, uncovered payers. But smallness brings two traps: the sample cannot support inference, and the definition choice decides the result. The whole workflow is built around those two.

## Stage 0: test whether the data can carry the question

Before writing anything, split the question into three conditions and verify each in the data. If one fails, change the question or the database. Do not force it.

| Condition | Ask | Sign of failure |
|---|---|---|
| Identifiable | Can the subgroup be pulled out at event or person level, and by which variable and code | Only free text, or a chain of inferences resting on assumptions |
| Observable | Is the outcome (payment, use, health) recorded for this group, and how complete is it | Outcome exists only for the mainstream; the subgroup is largely missing |
| Large enough | Does the unweighted count support the comparison you want | After splitting into periods, single digits remain |

**Count before you design.** Run the narrowest identifiable definition and record unweighted n, the number of primary sampling units involved, and the number of strata. Those three numbers decide everything downstream. Never design a model and then check whether the data suffice.

**Separate the statutory from the empirical.** A conclusion readable directly from a rule (what the text says, who is excluded) needs no test; it is a statutory claim. A conclusion requiring data (whether the rule operates in practice) is an empirical claim. Blending them means a null result reads as "contrary to expectation" when in fact nothing was tested. Say in the text which one you are testing.

## Stage 1: locate the subgroup, one codebook at a time

The first killer in multi-year data is change in variables and categories. **Check the codebook for every year separately; never apply the last year's definition across the series.**

Five things to check:

1. **Renamed variables.** A rename usually accompanies a recoding of the whole category set.
2. **Changed category values.** The same concept can carry different codes in different years; filtering by value across years silently drops half the period.
3. **Original versus re-release.** Some years are re-released because the first release over-suppressed fields, folding codes into other categories. Counting from the original release can return zero.
4. **File-type confusion.** Series with similar names mix inpatient, office-based, outpatient department and ancillary files, sometimes differing by one letter. Downloading the wrong one raises no error; it just makes the results strange.
5. **Negative codes.** Minus one often means "not applicable" rather than missing; minus eight, minus nine and minus fifteen mean don't know, not ascertained and cannot be computed. Treating "not applicable" as missing deletes a valid block and changes the denominator.

After checking, put a year-by-year table in the appendix: year, file name, variable name, category values, event count. This is the first thing a reviewer looks at and the only record you will have when reproducing your own work.

## Stage 2: parameterise the definition, never keep only one

Identifying a small subgroup almost always crosses three independent dimensions: **who counts (identification)**, **which occasion counts (attribution)**, and **which source counts (file)**. Give each dimension two to five values and cross them all.

The full cross is not decoration. It answers how far the conclusion depends on the definition. Report three things:

- **Main specification**, fixed before results exist, on grounds of sample size and interpretability, not the size of the estimate.
- **Sensitivity**, the remaining combinations compared item by item, showing which conclusion turns.
- **A genuinely disjoint definition.** At least one value must not contain the others. If the values nest (A inside B, C equal to B), you have one set of numbers and the sensitivity analysis is empty. A reviewer will ask.

**State the equivalences explicitly.** Which values reproduce each other, why, and that they are retained so readers can verify the containment themselves. Without that, the exercise looks like padding.

## Stage 3: health-check the size and the precision

The commonest error with small data is running a period comparison on twenty observations. Set three thresholds, write them into the code, and do not move them after seeing results:

- **Small cell**: unweighted n below a set value (fifty, for example) is flagged and not interpreted alone.
- **Unreliable variance**: fewer than ten primary sampling units in the domain.
- **Inestimable variance**: a single PSU in the domain; report the point estimate and say the interval cannot be computed.

PSUs must be counted **within the domain**, not in the full sample. This is the easiest place to be wrong: using the full-sample count overstates precision.

When an interval crosses zero, write "a change cannot be excluded", not "there is no difference". The first is about precision, the second about effect. The second requires an equivalence test.

## Stage 4: understand how the outcome variable was manufactured

Payment, cost and outcome variables are often missing or imputed for small groups. Three checks:

1. **Do the components sum to the total?** Add the components, compare with the official total, and trace every discrepancy. A gap means an unclassified category or a different definition.
2. **Imputation status.** Most surveys flag imputation per variable. Compute the same indicator on the fully reported subset and on the full set. A threefold gap is normal, and the gap itself belongs in the main text, not only in the appendix.
3. **Zeros and negatives.** A zero or negative total may be a real economic event or a coding artefact; the codebook decides. Do not delete by default.

**Handle unlinked and unmatched records separately**: compare them with linked records on the outcome, then report bounds under worst-case assumptions. The bound is often more persuasive than the point estimate.

## Stage 5: weights and variance

- Use the official weights; do not construct your own. In event files each row is an event and carries the person's annual weight, so event totals estimate events and the variance comes from person-level strata and PSUs.
- Single-year analyses use that year's stratum and PSU variables; pooled analyses use the official pooled structure where one exists, with weights scaled by the number of years.
- For proportions in small samples use an exact method (such as the survey version of Clopper-Pearson). A normal approximation will produce negative lower bounds.
- Two-period differences: the periods are independent samples, so add the variances. Longitudinal comparisons within the same sample need covariance adjustment; do not mix the two.

## Stage 6: discontinuities and the counterfactual

Small-subgroup studies often borrow a policy discontinuity. Three rules:

- Anchor the date to a file number and an effective date, not "around 2020".
- Report the minimum sample in each period. If it is too small, say that a period comparison is not possible and describe the full period instead.
- Ask whether the policy acts on the same object you are comparing. If the policy targets one indication while you compare the total with another, that channel is invisible by design. That is an explanation to write into the discussion, not a failure.

## Stage 7: layer the conclusions

After the results, list what can be said and what cannot:

| Layer | Example | Strength |
|---|---|---|
| Volume | how many events or people per year | strongest; depends only on identification and weights |
| Structure | payment composition, out-of-pocket share | moderate; depends on components and imputation |
| Change | difference across the discontinuity | weak; depends on precision |
| Cause | what the policy produced | usually out of reach without a design |

The higher the layer, the tighter the wording. **Do not rescue a result with "although the sample is limited, the trend is clear".** A limited sample is limited.

## Stage 8: package for reproduction

Reviewers and editors must be able to produce the same numbers. Provide at least five things:

1. File inventory: year, file name, contents, rows.
2. Variable map: variable names by year, category values.
3. Construction sequence: every step from raw file to analysis file, with merge keys and de-duplication rules.
4. Specification table: the operational definition and event count for every value of every dimension.
5. Code: build, specification matrix, tables and figures as separate files, with path variables that can be overridden, not tied to the author's directories.

Do not put typesetting scripts in the appendix. The code must reproduce every number in the text; if it cannot, the work is not finished.

## Stage 9: reporting discipline

- Every estimate carries an unweighted n, or a numerator and denominator.
- Write "cannot be confirmed" where it cannot; never "warrants further research".
- Flag small cells; do not interpret them alone, and do not quietly merge them into a larger group to hide them.
- Where a definition choice is unrelated to the result, say the basis was sample size and interpretability.
- Put limitations where the method is described, not as a disclaimer after the conclusion.

## Trap table

| Symptom | Cause | Check |
|---|---|---|
| A year with zero counts | Wrong file type, or an over-suppressed original release | Recompute with the correct file; read the re-release note |
| An unexplained step between years | Variable recoding | Year-by-year codebook check; note it in the table footnote |
| An odd denominator | "Not applicable" treated as missing | Read each negative code's meaning |
| Interval narrower than expected | Full-sample PSUs used instead of domain PSUs | Recompute within the domain |
| Coverage rate changes threefold | Imputed and full samples mixed | Report both subsets side by side |
| Sensitivity analysis shows nothing | Values nest inside each other | Add a genuinely disjoint value |
| Conclusion flips with one change of definition | Main specification chosen after seeing results | Write the basis before the results exist |

## What to say when delivering

- Whether each of the three conditions was met, and on what number
- Unweighted n, domain PSUs, interval width
- What the main specification is, why, and whether any combination turns the result
- Which quantities can be confirmed, which can only be described, which cannot be touched
- What reproduction requires, and what is missing
"""

import argparse
import os
import sys

NAME = "niche-data-workflow"


def check():
    problems = []
    if not CONTENT.startswith("---"):
        problems.append("missing YAML header")
    if "name: " + NAME not in CONTENT:
        problems.append("name in YAML header does not match")
    if "description:" not in CONTENT:
        problems.append("missing description in YAML header")
    sections = [l for l in CONTENT.splitlines() if l.startswith("## ")]
    if len(sections) < 5:
        problems.append("expected at least 5 sections, found %d" % len(sections))
    if len(CONTENT) < 6000:
        problems.append("content looks truncated (%d characters)" % len(CONTENT))
    return problems, len(sections)


def write(target_dir):
    out_dir = os.path.join(target_dir, NAME)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "SKILL.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(CONTENT)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Install the %s skill." % NAME)
    ap.add_argument("--dir", default=".", help="parent directory for the skill folder")
    ap.add_argument("--print", dest="do_print", action="store_true", help="print the skill text")
    ap.add_argument("--check", action="store_true", help="verify the embedded text")
    args = ap.parse_args(argv)

    if args.do_print:
        sys.stdout.write(CONTENT)
        return 0

    problems, n_sections = check()
    if args.check:
        if problems:
            print("FAIL")
            for p in problems:
                print("  -", p)
            return 1
        print("OK  %s  %d characters, %d sections" % (NAME, len(CONTENT), n_sections))
        return 0

    if problems:
        print("warning: " + "; ".join(problems), file=sys.stderr)
    path = write(args.dir)
    print("written:", os.path.abspath(path))
    print("next: put the folder %s into your skills directory." % NAME)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
