from dataclasses import dataclass


@dataclass(frozen=True)
class Initiative:
    name: str
    team: str
    decision: str
    reason: str
    tradeoff: str
    insight: str
    quote: str
    strategy: str
    gate: str
    metric: str
    handoff: str


INITIATIVES = (
    Initiative(
        name="Guided setup",
        team="Activation",
        decision="Guided setup starts with inviting a teammate before importing a CSV.",
        reason="Solo trial users abandoned the importer when they lacked a sample file, while "
        "a teammate invitation created a collaborative first session.",
        tradeoff="CSV import remains accessible from the checklist after setup.",
        insight="Trial admins wanted to see a useful workspace before preparing their data.",
        quote="I have to ask operations for a spreadsheet, but I can invite another admin today.",
        strategy="Pilot invite-first onboarding with new self-serve trials, then add assisted "
        "setup for teams with an assigned implementation lead.",
        gate="Let an owner skip invitations and continue to the sample workspace.",
        metric="Track the share of trials with two active teammates in the first seven days.",
        handoff="Support owns the sample workspace link and the skipped-invite recovery steps.",
    ),
    Initiative(
        name="Activity digest",
        team="Engagement",
        decision="The activity digest ships as a weekly opt-in email on Mondays.",
        reason="Daily messages duplicated in-app updates and buried the decisions readers "
        "needed to catch up on after the weekend.",
        tradeoff="Real-time notifications remain available for directly assigned work.",
        insight="People wanted to catch up after time away without getting another daily feed.",
        quote="I want one Monday email after a trip, not five copies of the activity feed.",
        strategy="Pilot the weekly recap with low-frequency collaborators before offering it "
        "to administrators who already manage notification policies.",
        gate="Respect the workspace timezone and suppress emails during a user pause.",
        metric="Track unsubscribes per thousand weekly sends alongside recap return visits.",
        handoff="Support owns the unsubscribe macro and the Monday delivery escalation path.",
    ),
    Initiative(
        name="Expiring share links",
        team="Trust",
        decision="Public share links expire after seven days by default.",
        reason="Agency reviews usually finish inside a week, while permanent URLs kept old "
        "client work reachable after engagements ended.",
        tradeoff="Owners can deliberately extend an active link from the sharing dialog.",
        insight="Agency coordinators needed clients to review a file without creating accounts.",
        quote="Our reviewers hate logins, but I don't want last year's link left lying around.",
        strategy="Pilot expiration with client-review agencies, then extend the controls "
        "to regulated workspaces after the policy UI review.",
        gate="Expired links show the viewer how to ask the owner for a fresh link.",
        metric="Track expired-link reopen requests per hundred external reviews.",
        handoff="Support owns the expired-link reply and the owner renewal walkthrough.",
    ),
    Initiative(
        name="Renewal dashboard",
        team="Accounts",
        decision="The renewal dashboard leads with usage trends and shows billing lag separately.",
        reason="A delayed invoice previously made healthy accounts appear to have stopped "
        "adopting the product.",
        tradeoff="The dashboard shows invoice status for reconciliation in a secondary panel.",
        insight="Account leads looked for quiet teams several weeks before a contract ended.",
        quote="A red invoice tells me about finance. I need to know when a team stopped logging in.",
        strategy="Pilot with account leads managing quarterly renewals before adding a "
        "portfolio view for regional managers.",
        gate="Label the most recent usage refresh beside the account trend.",
        metric="Track active-day coverage across accounts within sixty days of renewal.",
        handoff="Support owns the stale-usage runbook and finance owns invoice corrections.",
    ),
    Initiative(
        name="Intake board",
        team="Workflows",
        decision="The intake board suggests possible duplicates before a request enters triage.",
        reason="Reviewers routinely merged the same request by hand across multiple queues.",
        tradeoff="Reporters can file a separate request when a matching item has a different scope.",
        insight="Requesters wanted to keep their original note visible when joining a prior request.",
        quote="I don't mind joining a duplicate as long as my customer's details aren't lost.",
        strategy="Pilot duplicate suggestions on the internal request queue before exposing "
        "suggestions on external forms.",
        gate="Preserve the reporter's original comment when they follow a suggested match.",
        metric="Track reviewer triage minutes per accepted intake request.",
        handoff="Support owns the wrong-merge escalation and the restore-original-note checklist.",
    ),
    Initiative(
        name="Audit export",
        team="Trust",
        decision="Audit exports include both a UTC timestamp and the actor's display timezone.",
        reason="Investigators needed a common timeline while local reviewers compared events "
        "with incident notes recorded in their own timezones.",
        tradeoff="The authoritative sort order uses UTC even when the report displays local time.",
        insight="Compliance reviewers struggled to align a downloaded log with incident notes.",
        quote="The spreadsheet said 4:15, and nobody could tell me whether it meant London or UTC.",
        strategy="Pilot with security reviewers who run monthly evidence checks, then "
        "stabilize the CSV columns for recurring exports.",
        gate="A daylight saving transition must round-trip without dropping an offset.",
        metric="Track the fraction of evidence reviews completed without timezone clarification.",
        handoff="Support owns the UTC comparison example and the evidence-export field glossary.",
    ),
    Initiative(
        name="Saved views",
        team="Workflows",
        decision="A saved view is personal by default and requires an explicit action to share.",
        reason="Stale experimental filters accumulated when every new view was published to the team.",
        tradeoff="Team leads can still pin shared views as defaults for new workspace members.",
        insight="People wanted freedom to try filters without adding clutter to teammates' menus.",
        quote="My drill-down is useful to me, but it shouldn't show up in everyone else's sidebar.",
        strategy="Pilot personal views with operators doing daily reviews before opening "
        "team templates to managers.",
        gate="Show who can see the view before the owner confirms sharing.",
        metric="Track personal views used on at least two different days within a week.",
        handoff="Support owns the missing-view checklist and the unshare instructions.",
    ),
    Initiative(
        name="Workspace handoff",
        team="Accounts",
        decision="Workspace handoff requires the incoming owner to accept before access transfers.",
        reason="Silent ownership changes stranded scheduled work when the recipient was away "
        "or the wrong person was selected.",
        tradeoff="The current owner keeps control while the confirmation is pending.",
        insight="Departing admins wanted proof that somebody could maintain their scheduled work.",
        quote="I can nominate someone on Friday, but I don't know whether they saw the handover.",
        strategy="Pilot on planned admin departures, then support emergency transfers after "
        "an escalation and recovery review.",
        gate="Require a backup contact and send a reminder after forty-eight hours.",
        metric="Track completed transfers within two business days of a request.",
        handoff="Support owns pending-transfer reminders and the backup-contact recovery guide.",
    ),
    Initiative(
        name="Usage alerts",
        team="Billing",
        decision="Usage alerts send one early warning at eighty percent of the monthly allowance.",
        reason="A warning at the limit gave teams too little time to redistribute or approve spend.",
        tradeoff="The early warning repeats only after the monthly allowance resets.",
        insight="Budget owners needed enough lead time to discuss an upgrade at their weekly meeting.",
        quote="A warning at the ceiling is already too late for me to get a purchase approved.",
        strategy="Pilot with fixed-cap teams before supporting pooled allowances and custom thresholds.",
        gate="Suppress multiple warnings when usage fluctuates near the threshold.",
        metric="Track cap breaches that had an acknowledged early warning before the breach.",
        handoff="Support owns allowance explanations and billing owns meter reconciliation.",
    ),
    Initiative(
        name="Mobile approvals",
        team="Engagement",
        decision="Mobile approvals show a preview and require a reason when rejecting a request.",
        reason="People on phones dismissed ambiguous requests and left requesters guessing "
        "whether to edit or resubmit.",
        tradeoff="Approvals can be confirmed with one tap after opening the preview.",
        insight="On-call approvers wanted enough context to act while away from their desks.",
        quote="If I can see the impact and explain a no, I don't need to wait for my laptop.",
        strategy="Pilot with on-call approvers handling time-sensitive requests before "
        "adding bulk actions for managers.",
        gate="When offline, retain the draft reason and make the unsent state visible.",
        metric="Track median time to a mobile decision and the rate of reopened requests.",
        handoff="Support owns the offline approval checklist and the resubmission guidance.",
    ),
)
