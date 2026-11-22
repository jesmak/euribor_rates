import { describe, expect, it } from "vitest";

import { addMonths, availableRanges, changes, periodsFrom, points, steps } from "../src/series";
import type { Point } from "../src/series";

describe("days", () => {
    it("are the statistics rows' days in Home Assistant's time zone", () => {
        // Midnight in Helsinki, which is the evening before in UTC.
        const rows = [
            { start: Date.parse("2026-11-18T22:00:00Z"), mean: 3.343 },
            { start: Date.parse("2026-11-17T22:00:00Z"), mean: 3.351 },
            { start: Date.parse("2026-11-16T22:00:00Z"), mean: null },
        ];
        expect(points(rows, "Europe/Helsinki")).toEqual([
            { day: "2026-11-18", value: 3.351 },
            { day: "2026-11-19", value: 3.343 },
        ]);
    });

    it("add months on the same day of the month or the month's last, as the integration does", () => {
        expect(addMonths("2026-01-31", 1)).toBe("2026-02-28");
        expect(addMonths("2028-01-31", 1)).toBe("2028-02-29");
        expect(addMonths("2026-08-27", 12)).toBe("2027-08-27");
        expect(addMonths("2026-03-31", -1)).toBe("2026-02-28");
        expect(addMonths("2026-01-15", -1)).toBe("2025-12-15");
    });
});

describe("ranges", () => {
    const history = (first: string): Point[] => [
        { day: first, value: 2 },
        { day: "2026-11-19", value: 3 },
    ];

    it("show only what the history covers, with a few days' slack for a first day that fell on a weekend", () => {
        expect(availableRanges(history("2025-11-24"), "2026-11-22")).toEqual(["1m", "1y", "all"]);
        expect(availableRanges(history("2025-12-01"), "2026-11-22")).toEqual(["1m", "all"]);
        expect(availableRanges(history("2021-11-22"), "2026-11-22")).toEqual(["1m", "1y", "2y", "3y", "5y", "all"]);
        expect(availableRanges([], "2026-11-22")).toEqual([]);
    });
});

describe("changes", () => {
    it("are the newest rate less the one a month and a year earlier", () => {
        const series: Point[] = [
            { day: "2025-11-19", value: 2.229 },
            { day: "2026-10-16", value: 3.215 },
            { day: "2026-10-19", value: 3.233 },
            { day: "2026-11-19", value: 3.343 },
        ];
        const { month, year } = changes(series);
        expect(month).toBeCloseTo(0.11, 6);
        expect(year).toBeCloseTo(1.114, 6);
    });

    it("leave out a change the history doesn't reach", () => {
        expect(
            changes(
                [
                    { day: "2026-11-19", value: 3.343 },
                    { day: "2026-10-01", value: 3 },
                ].reverse(),
            ).year,
        ).toBeUndefined();
    });
});

describe("lock periods", () => {
    it("are the integration's answer, with anything malformed left out", () => {
        const answer = {
            periods: [
                { reset: "2025-10-05", until: "2026-10-05", rate_date: "2025-10-03", rate: 2.224 },
                { reset: "2026-10-05", until: "2027-10-05", rate_date: "2026-10-05", rate: "3.186" },
                { reset: "2026-10-05", until: "2027-10-05", rate_date: null, rate: 3.186 },
            ],
        };
        expect(periodsFrom(answer)).toEqual([{ reset: "2025-10-05", until: "2026-10-05", locked: { day: "2025-10-03", value: 2.224 } }]);
        expect(periodsFrom(undefined)).toEqual([]);
        expect(periodsFrom({ periods: "none" })).toEqual([]);
    });
});

describe("steps", () => {
    it("are the days the rate changed", () => {
        const ecb: Point[] = [
            { day: "2026-06-16", value: 2 },
            { day: "2026-06-17", value: 2.25 },
            { day: "2026-09-15", value: 2.25 },
            { day: "2026-09-16", value: 2.5 },
        ];
        expect(steps(ecb)).toEqual([
            { day: "2026-06-17", from: 2, to: 2.25 },
            { day: "2026-09-16", from: 2.25, to: 2.5 },
        ]);
    });
});
