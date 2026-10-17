"use client";

import { FormEvent, useState } from "react";

type Opportunity = {
  title: string;
  organisation: string;
  domain: string;
  type: "Research project" | "Industry internship";
  description: string;
  apply_url: string;
  source_name: string;
  source_url: string;
};

type OpportunityResponse = {
  domain: string;
  opportunities: Opportunity[];
  warnings: string[];
  fetched_at: string;
};

const DOMAINS = [
  { value: "cse", label: "Computer Science" },
  { value: "electrical", label: "Electrical Engineering" },
  { value: "mechanical", label: "Mechanical Engineering" },
];

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

function OpportunityCards({ opportunities }: { opportunities: Opportunity[] }) {
  return (
    <div className="card-grid">
      {opportunities.map((opportunity, index) => {
        const isIndustryInternship = opportunity.type === "Industry internship";
        return (
          <article className="opportunity-card" key={`${opportunity.apply_url}-${index}`}>
            <span className={`tag ${isIndustryInternship ? "industry" : "research"}`}>
              {opportunity.type}
            </span>
            <h3>{opportunity.title}</h3>
            <p className="organisation">{opportunity.organisation}</p>
            <p className="description">{opportunity.description}</p>
            <p className="source">Source: {opportunity.source_name}</p>
            <a href={opportunity.apply_url} target="_blank" rel="noreferrer">
              {isIndustryInternship ? "View internship" : "View project"} <span aria-hidden="true">↗</span>
            </a>
          </article>
        );
      })}
    </div>
  );
}

export default function Home() {
  const [domain, setDomain] = useState("cse");
  const [results, setResults] = useState<OpportunityResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const industryOpportunities = results?.opportunities.filter(
    (opportunity) => opportunity.type === "Industry internship",
  ) ?? [];
  const researchOpportunities = results?.opportunities.filter(
    (opportunity) => opportunity.type === "Research project",
  ) ?? [];

  async function findOpportunities(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError("");
    setResults(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/opportunities?domain=${encodeURIComponent(domain)}`,
      );
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail ?? "The server could not find opportunities.");
      }

      setResults(data);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Something went wrong.";
      setError(`Could not fetch opportunities. ${message}`);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main>
      <section className="hero">
        <p className="eyebrow">PEERSPACE · OPPORTUNITY DISCOVERY</p>
        <h1>Find a project that gets you started.</h1>
        <p className="intro">
          Pick your engineering domain to discover public research projects and industry internships.
        </p>

        <form className="search-form" onSubmit={findOpportunities}>
          <label htmlFor="domain">Your domain</label>
          <div className="form-row">
            <select id="domain" value={domain} onChange={(event) => setDomain(event.target.value)}>
              {DOMAINS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <button type="submit" disabled={isLoading}>
              {isLoading ? "Looking..." : "Find opportunities"}
            </button>
          </div>
        </form>
      </section>

      <section className="results" aria-live="polite">
        {isLoading && <p className="status">Checking public sources for current opportunities...</p>}

        {error && (
          <div className="message error-message">
            <strong>Search failed.</strong> {error} Make sure the FastAPI server is running, then try again.
          </div>
        )}

        {results && (
          <>
            <div className="results-heading">
              <div>
                <p className="eyebrow">RESULTS</p>
                <h2>Opportunities for {DOMAINS.find((item) => item.value === results.domain)?.label}</h2>
              </div>
              <p className="fetched-time">Fetched {new Date(results.fetched_at).toLocaleTimeString()}</p>
            </div>

            {results.warnings.length > 0 && (
              <div className="message warning-message">
                <strong>Some sources were unavailable.</strong> {results.warnings.join(" ")}
              </div>
            )}

            {results.opportunities.length === 0 ? (
              <p className="status">No readable listings were found. Try again later or open the source pages directly.</p>
            ) : (
              <div className="result-groups">
                {industryOpportunities.length > 0 && (
                  <section>
                    <h3 className="section-heading">Industry internships ({industryOpportunities.length})</h3>
                    <OpportunityCards opportunities={industryOpportunities} />
                  </section>
                )}
                {researchOpportunities.length > 0 && (
                  <section>
                    <h3 className="section-heading">Research projects ({researchOpportunities.length})</h3>
                    <OpportunityCards opportunities={researchOpportunities} />
                  </section>
                )}
              </div>
            )}
          </>
        )}
      </section>
    </main>
  );
}
