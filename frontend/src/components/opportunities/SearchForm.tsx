
"use client";

import type { DomainOption } from "@/types/opportunity";

import { Button } from "@/components/ui/button";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

type SearchFormProps = {
    domain: string;
    domains: DomainOption[];
    isLoading: boolean;
    onDomainChange: (domain: string) => void;
    onSearch: () => void;
};

export default function SearchForm({
    domain,
    domains,
    isLoading,
    onDomainChange,
    onSearch,
}: SearchFormProps) {
    return (
        <form
            onSubmit={(event) => {
                event.preventDefault();
                onSearch();
            }}
            className="max-w-3xl"
        >
            <label
                htmlFor="domain"
                className="mb-2 block text-sm font-semibold"
            >
                Your engineering domain
            </label>

            <div className="flex flex-col gap-3 sm:flex-row">
                <Select
                    value={domain}
                    onValueChange={(value) => {
                        if (value !== null) {
                            onDomainChange(value);
                        }
                    }}
                >
                    <SelectTrigger
                        id="domain"
                        className="h-12 flex-1 border-white/30 bg-white text-slate-900"
                    >
                        <SelectValue placeholder="Choose your domain" />
                    </SelectTrigger>

                    <SelectContent>
                        {domains.map((option) => (
                            <SelectItem
                                key={option.value}
                                value={option.value}
                            >
                                {option.label}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>

                <Button
                    type="submit"
                    disabled={isLoading}
                    className="h-12 bg-orange-600 px-6 font-semibold text-white hover:bg-orange-700"
                >
                    {isLoading ? "Looking..." : "Find opportunities"}
                </Button>
            </div>
        </form>
    );
}
