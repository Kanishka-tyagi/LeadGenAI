import { useEffect, useMemo, useState } from "react";
import type { Lead, LeadListResponse, LeadStatus } from "../api/types";
import { effectiveScore } from "../api/types";
async function fetchLeads(): Promise<LeadListResponse> {
  const res = await fetch("/api/leads");
  return res.json();
}

const STATUS_OPTIONS: (LeadStatus | "all")[] = [
  "all",
  "new",
  "scored",
  "reviewed",
  "contacted",
  "converted",
  "rejected",
];

export default function Dashboard() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<LeadStatus | "all">("all");
  const [minScore, setMinScore] = useState(0);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    fetchLeads().then((res) => {
      setLeads(res.items);
      setLoading(false);
    });
  }, []);

  const filtered = useMemo(() => {
    return leads
      .filter((l) => statusFilter === "all" || l.status === statusFilter)
      .filter((l) => effectiveScore(l) >= minScore)
      .filter((l) =>
        search.trim() === ""
          ? true
          : l.business_name.toLowerCase().includes(search.toLowerCase())
      )
      .sort((a, b) => effectiveScore(b) - effectiveScore(a));
  }, [leads, statusFilter, minScore, search]);

  const selected = leads.find((l) => l.id === selectedId) ?? null;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Leads</h1>
        <div className="filters">
          <input
            placeholder="Search business name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as LeadStatus | "all")}
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s === "all" ? "All statuses" : s}
              </option>
            ))}
          </select>
          <label>
            Min score
            <input
              type="range"
              min={0}
              max={100}
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
            />
            {minScore}
          </label>
        </div>
      </header>

      <div className="dashboard-body">
        <table className="lead-table">
          <thead>
            <tr>
              <th>Business</th>
              <th>Category</th>
              <th>Website</th>
              <th>Score</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={5}>Loading...</td>
              </tr>
            )}
            {!loading &&
              filtered.map((lead) => (
                <tr
                  key={lead.id}
                  onClick={() => setSelectedId(lead.id)}
                  className={selectedId === lead.id ? "selected" : ""}
                >
                  <td>{lead.business_name}</td>
                  <td>{lead.category ?? "—"}</td>
                  <td>{lead.website_url ? "Yes" : "No"}</td>
                  <td>
                    <ScoreBadge score={effectiveScore(lead)} />
                  </td>
                  <td>{lead.status}</td>
                </tr>
              ))}
            {!loading && filtered.length === 0 && (
              <tr>
                <td colSpan={5}>No leads match these filters.</td>
              </tr>
            )}
          </tbody>
        </table>

        {selected && <LeadDetailPanel lead={selected} />}
      </div>
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const tier = score >= 70 ? "high" : score >= 40 ? "mid" : "low";
  return <span className={`score-badge score-${tier}`}>{score}</span>;
}

function LeadDetailPanel({ lead }: { lead: Lead }) {
  const [emailBody, setEmailBody] = useState(
    lead.edited_email_body ?? lead.llm_output?.drafted_email_body ?? ""
  );

  return (
    <aside className="lead-detail">
      <h2>{lead.business_name}</h2>
      <p className="muted">{lead.address}</p>

      <section>
        <h3>Score breakdown</h3>
        {lead.llm_output ? (
          <ul className="score-breakdown">
            <li>Website score: {lead.llm_output.website_score}</li>
            <li>Digital presence: {lead.llm_output.digital_presence}</li>
            <li>
              <strong>Overall: {effectiveScore(lead)}</strong>
              {lead.overridden_score != null && " (overridden)"}
            </li>
          </ul>
        ) : (
          <p className="muted">Not scored yet — no website analysis available.</p>
        )}
      </section>

      {lead.sub_scores && (
        <section>
          <h3>Signals</h3>
          <ul>
            <li>Has website: {lead.sub_scores.has_website ? "Yes" : "No"}</li>
            {lead.sub_scores.mobile_responsive != null && (
              <li>Mobile responsive: {lead.sub_scores.mobile_responsive ? "Yes" : "No"}</li>
            )}
            {lead.sub_scores.broken_links_count != null && (
              <li>Broken links: {lead.sub_scores.broken_links_count}</li>
            )}
            {lead.sub_scores.outdated_tech_flags.length > 0 && (
              <li>Flags: {lead.sub_scores.outdated_tech_flags.join(", ")}</li>
            )}
          </ul>
        </section>
      )}

      {lead.llm_output && (
        <section>
          <h3>Drafted email</h3>
          <p className="muted">{lead.llm_output.drafted_email_subject}</p>
          <textarea
            rows={8}
            value={emailBody}
            onChange={(e) => setEmailBody(e.target.value)}
          />
          <button onClick={() => alert("Wire this up to PATCH /leads/{id}")}>
            Save & approve
          </button>
        </section>
      )}
    </aside>
  );
}