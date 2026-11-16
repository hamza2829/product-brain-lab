"""Write a reproducible JSONL corpus for the fictional Aster Quay product team."""

import argparse
import random
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path

from product_brain_lab.corpus import Document, Source
from product_brain_lab.initiatives import INITIATIVES, Initiative

DEFAULT_SEED = 43
DEFAULT_DATA_DIR = Path("data/synthetic")
FIRST_DATE = date(2025, 1, 6)
WRITERS = ("Mira Sol", "Devon Marr", "Lina Rook", "Tess Fen", "Kai Orlan", "Niko Vale")
SOURCE_LAYOUT = {
    Source.JIRA: ("JIRA", 15),
    Source.CONFLUENCE: ("CF", 4),
    Source.SLACK: ("SLACK", 20),
    Source.SHAREPOINT: ("SP", 2),
}

TICKET_WORK = (
    (
        "Review empty state",
        "Run the primary flow in a workspace with no activity and record the next action.",
    ),
    (
        "Add event names",
        "Confirm the event payload has a workspace identifier and phase, then update the dictionary.",
    ),
    (
        "Review permissions",
        "Check the difference between a workspace owner and a read-only collaborator.",
    ),
    (
        "Confirm billing copy",
        "Ask the billing team to review the labels on settings and the help link.",
    ),
    (
        "Keyboard and focus pass",
        "Walk through the dialog with a keyboard and check the initial focus target.",
    ),
    (
        "Draft release note",
        "Put a one-paragraph explanation and a screenshot in the internal release queue.",
    ),
    (
        "Localize status copy",
        "Send the success and pending labels to localization with character limits.",
    ),
    (
        "Check event delivery",
        "Compare test workspace event counts between the client log and the reporting view.",
    ),
    (
        "Prepare a QA fixture",
        "Create a second sample workspace with a previous phase and run the regression list.",
    ),
    ("Record flag owner", "Confirm who can widen the rollout and capture the rollback location."),
    (
        "Review response time",
        "Check the oldest sample workspace and keep timings in the launch record.",
    ),
    (
        "Confirm settings reset",
        "Restore default settings and confirm historical entries remain readable.",
    ),
    (
        "Close pilot access",
        "Remove the temporary test group after the team reviews the pilot notes.",
    ),
)

THREAD_TOPICS = (
    (
        "Copy review",
        "The current button label repeats the dialog heading. Can we label the actual action?",
    ),
    (
        "Release calendar",
        "The internal demo moved to Thursday. Add anything you want the hosts to show.",
    ),
    (
        "Test workspace",
        "I refreshed the test workspace so the next walkthrough can start with a clean history.",
    ),
    (
        "Permission check",
        "Please include the collaborator role in the next dry run. Owners passed yesterday.",
    ),
    (
        "Dashboard review",
        "The chart title in the draft is vague. Add the cohort and the time window.",
    ),
    (
        "Meeting notes",
        "The pilot notes are ready. Please add any open questions before the next review.",
    ),
    ("Handoff checklist", "Can someone confirm who has the link to the internal walkthrough?"),
    (
        "QA replay",
        "I can reproduce the empty state with fixture B. I'll add a screenshot to the ticket.",
    ),
    (
        "Release note draft",
        "Keep the release note to one paragraph. The workflow details go in the guide.",
    ),
    (
        "Design follow-up",
        "I left comments on the error and pending states. The happy path is ready to review.",
    ),
    (
        "Pilot change window",
        "Leave the current cohort in place until the next group has finished onboarding.",
    ),
    (
        "Office hours",
        "We have one office-hours slot left. I can take questions from the pilot team then.",
    ),
    (
        "Status check",
        "Please put the next checkpoint on the calendar before people rotate off this week.",
    ),
    (
        "Glossary edit",
        "Use the same settings label in the guide, the product, and the support macro.",
    ),
    (
        "Test recording",
        "The walkthrough recording has captions now. The preview is in the working folder.",
    ),
    (
        "Accessibility follow-up",
        "The narrow viewport looked good. Can we also try at 200 percent zoom?",
    ),
    ("Archive review", "I'm collecting outdated screenshots for removal after the pilot closes."),
)


def source_id(source: Source, initiative_index: int, slot: int) -> str:
    prefix, count = SOURCE_LAYOUT[source]
    return f"{prefix}-{initiative_index * count + slot:03d}"


def initiative_documents(
    initiative: Initiative, index: int, rng: random.Random
) -> Iterator[Document]:
    start = FIRST_DATE + timedelta(days=index * 19 + rng.randrange(3))
    name, team = initiative.name, initiative.team
    decision, insight, strategy, scorecard = (
        source_id(Source.CONFLUENCE, index, slot) for slot in range(1, 5)
    )
    acceptance, rollout = (source_id(Source.JIRA, index, slot) for slot in (1, 2))
    decision_thread, interview, handoff_thread = (
        source_id(Source.SLACK, index, slot) for slot in range(1, 4)
    )
    playbook, measures = (source_id(Source.SHAREPOINT, index, slot) for slot in (1, 2))

    def record(
        source: Source,
        slot: int,
        day: int,
        kind: str,
        title: str,
        body: str,
        *links: str,
    ) -> Document:
        return Document(
            id=source_id(source, index, slot),
            source=source,
            date=start + timedelta(days=day),
            initiative=name,
            kind=kind,
            title=title,
            body=body,
            author=rng.choice(WRITERS),
            related_ids=links,
        )

    yield record(
        Source.CONFLUENCE,
        1,
        5,
        "Decision",
        f"Decision record · {name}",
        f"{initiative.decision} {initiative.reason} {initiative.tradeoff}\n\n"
        f"The {team} team accepted this trade-off after reviewing the pilot notes. The scope "
        "applies to newly enrolled workspaces. Existing administrators will have time to "
        "review the change during office hours. We will revisit the decision after the first "
        "pilot review if the expected benefit does not appear in the cohort.\n\n"
        f"Implementation guardrail. {initiative.gate} Product will review the guardrail "
        "with support before the rollout widens.",
        insight,
        decision_thread,
        acceptance,
    )
    yield record(
        Source.CONFLUENCE,
        2,
        2,
        "Customer insight",
        f"Customer interviews · {name}",
        f"{initiative.insight}\n\nOne participant said, “{initiative.quote}”\n\n"
        "This theme surfaced in the discovery interviews. The team logged examples from "
        "first-time operators alongside feedback from more experienced admins. The research "
        "notes describe pain points and workarounds in the fictional interviews. The next "
        "review will check how often the pattern appears in the pilot cohort.",
        interview,
        decision,
    )
    yield record(
        Source.CONFLUENCE,
        3,
        8,
        "Strategy",
        f"Pilot strategy · {name}",
        f"{initiative.strategy}\n\nThe {team} team will review the initial cohort at its "
        "weekly meeting. Eligibility and communications will be documented in the release "
        "playbook. Any expansion requires a support walkthrough and an agreed owner for "
        "follow-up requests. Plan for one pilot cycle before setting a public timeline.",
        decision,
        playbook,
        rollout,
    )
    yield record(
        Source.CONFLUENCE,
        4,
        27,
        "Scorecard",
        f"Success measures · {name}",
        f"{initiative.metric} The pilot review also reviews support volume and compares "
        "behavior with the previous cohort. The baseline uses the same eligibility rules "
        "and reporting window. Treat changes in intervention or logging as a break in the "
        "series. The sheet has metric definitions. Results are pending.",
        measures,
        strategy,
    )

    yield record(
        Source.JIRA,
        1,
        9,
        "Story",
        f"Acceptance criteria · {name}",
        f"Verify the release guardrail before enrolling the next cohort. {initiative.gate}\n\n"
        f"The decision to implement is recorded as follows. {initiative.decision} "
        "Capture a successful run and a recovery path in the QA notes.",
        decision,
        rollout,
        handoff_thread,
    )
    yield record(
        Source.JIRA,
        2,
        12,
        "Task",
        f"Support handoff · {name}",
        f"{initiative.handoff} The ticket is ready to close once the receiving team completes "
        "a dry run and confirms the link to the release playbook.",
        playbook,
        handoff_thread,
        acceptance,
    )
    for slot, (title, task) in enumerate(TICKET_WORK, 3):
        yield record(
            Source.JIRA,
            slot,
            rng.randrange(10, 27),
            rng.choice(("Task", "Story", "QA")),
            f"{title} · {name}",
            f"{task}\n\nThe {team} team's working checklist links to the release criteria. "
            "Attach observations and tag the release owner if the plan needs to change.",
            acceptance,
            strategy,
        )

    yield record(
        Source.SLACK,
        1,
        5,
        "Decision thread",
        f"Decision recap · {name}",
        f"#{team.lower()}-product\n\nMira: {initiative.decision} {initiative.reason}\n"
        f"Kai: {initiative.tradeoff} I'll add that to the decision record before the review.",
        decision,
        acceptance,
    )
    yield record(
        Source.SLACK,
        2,
        3,
        "Research thread",
        f"Interview debrief · {name}",
        f"#customer-research\n\nLina: {initiative.insight} I wrote down one line verbatim. "
        f"“{initiative.quote}”\nTess: Let's check for this pattern again in the next interviews.",
        insight,
        strategy,
    )
    yield record(
        Source.SLACK,
        3,
        13,
        "Handoff thread",
        f"Support briefing · {name}",
        f"#release-support\n\nDevon: {initiative.handoff}\n"
        f"Kai: {initiative.gate} I've linked the dry-run ticket here for the release owner.",
        rollout,
        playbook,
        acceptance,
    )
    for slot, (title, note) in enumerate(THREAD_TOPICS, 4):
        yield record(
            Source.SLACK,
            slot,
            rng.randrange(4, 29),
            "Working thread",
            f"{title} · {name}",
            f"#{team.lower()}-product\n\n{rng.choice(WRITERS)}: {note}\n"
            f"{rng.choice(WRITERS)}: I'll follow up at the next checkpoint and update the linked item.",
            source_id(Source.JIRA, index, rng.randrange(3, 16)),
            strategy,
        )

    yield record(
        Source.SHAREPOINT,
        1,
        10,
        "Playbook",
        f"Release playbook · {name}",
        f"{initiative.strategy}\n\nSupport handoff. {initiative.handoff}\n\n"
        f"Before widening access, verify this guardrail. {initiative.gate} "
        "The release owner confirms nomination, pilot communications, and the rollback "
        "location during the readiness review.",
        strategy,
        rollout,
        handoff_thread,
    )
    yield record(
        Source.SHAREPOINT,
        2,
        25,
        "Measurement plan",
        f"Measurement worksheet · {name}",
        f"{initiative.metric}\n\nRecord cohort, eligibility, observed count, and denominator. "
        "Hold the comparison window fixed between release reviews. The analyst will flag "
        "missing observations and annotate changes to the instrumented event stream.",
        scorecard,
        strategy,
    )


def generate(directory: Path, seed: int = DEFAULT_SEED) -> dict[Source, int]:
    rng = random.Random(seed)
    documents = [
        doc
        for index, initiative in enumerate(INITIATIVES)
        for doc in initiative_documents(initiative, index, rng)
    ]
    ids = {doc.id for doc in documents}
    if len(ids) != len(documents) or any(set(doc.related_ids) - ids for doc in documents):
        raise ValueError("Synthetic IDs must be unique and all links must resolve")
    directory.mkdir(parents=True, exist_ok=True)
    counts = {}
    for source in Source:
        records = sorted((doc for doc in documents if doc.source == source), key=lambda doc: doc.id)
        (directory / f"{source.value}.jsonl").write_text(
            "".join(f"{doc.model_dump_json()}\n" for doc in records),
            encoding="utf-8",
            newline="\n",
        )
        counts[source] = len(records)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    counts = generate(args.out, args.seed)
    print(
        f"Wrote {', '.join(f'{count} {source}' for source, count in counts.items())} to {args.out}"
    )


if __name__ == "__main__":
    main()
