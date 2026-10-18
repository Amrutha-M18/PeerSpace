
"use client";

import { useState } from "react";

import Hero from "@/components/ui/Hero";

import SearchForm from "@/components/opportunities/SearchForm";
import OpportunityResults from "@/components/opportunities/OpportunityResults";

import { fetchOpportunities } from "@/lib/opportunities";

import type {
  DomainOption,
  OpportunityResponse,
} from "@/types/opportunity";

const DOMAINS: DomainOption[] = [
  { value: "cse", label: "Computer Science" },
  { value: "electrical", label: "Electrical Engineering" },
  { value: "mechanical", label: "Mechanical Engineering" },
];

export default function Home() {
  const [domain, setDomain] = useState("cse");

  const [results, setResults] =
    useState<OpportunityResponse | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function findOpportunities() {
    setIsLoading(true);
    setError("");
    setResults(null);

    try {
      const data = await fetchOpportunities(domain);
      setResults(data);
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "Something went wrong.";

      setError(`Could not fetch opportunities. ${message}`);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#fffdf7] text-slate-800">
      <section className="bg-linear-to-br from-[#14346b] via-[#2463be] to-[#3586dc] px-6 py-14 text-white sm:py-16 md:py-20">
        <div className="mx-auto max-w-5xl">
          <Hero />

          <SearchForm
            domain={domain}
            domains={DOMAINS}
            isLoading={isLoading}
            onDomainChange={setDomain}
            onSearch={findOpportunities}
          />
        </div>
      </section>

      <div className="mx-auto my-12 w-[calc(100%-3rem)] max-w-5xl md:my-16">
        <OpportunityResults
          results={results}
          isLoading={isLoading}
          error={error}
          domains={DOMAINS}
        />
      </div>
    </main>
  );
}
