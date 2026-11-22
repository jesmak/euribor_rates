import { describe, expect, it } from "vitest";

import { addMonths, availableRanges, changes, lockedOn, lockPeriods, points, steps } from "../src/series";
import type { Point } from "../src/series";

// Made-up rates around a Friday 18 December, a Christmas Friday 25 December and New Year's Day, with no rates on the
// weekends or holidays, as in the real statistics. The same days as the integration's own tests.
const RATES: Point[] = [
    { day: "2026-12-17", value: 2.41 },
    { day: "2026-12-18", value: 2.42 },
    { day: "2026-12-21", value: 2.43 },
    { day: "2026-12-24", value: 2.44 },
    { day: "2026-12-28", value: 2.45 },
];

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

describe("a reset's locked rate", () => {
    // The same cases as test_loans.py's for the integration's locked(), which this has to agree with.
    const cases: [string, Point[], string, number, Point | undefined][] = [
        ["the reset day's own once published", RATES, "2026-12-18", 0, RATES[1]],
        ["not before the day's rate is out", RATES.slice(0, 1), "2026-12-18", 0, undefined],
        ["a Saturday's is Friday's as soon as it is out", RATES.slice(0, 2), "2026-12-19", 0, RATES[1]],
        ["a Sunday's is Friday's as soon as it is out", RATES.slice(0, 2), "2026-12-20", 0, RATES[1]],
        ["a weekend's waits for Friday's", RATES.slice(0, 1), "2026-12-20", 0, undefined],
        ["a holiday's waits for a later day", RATES.slice(0, 4), "2026-12-25", 0, undefined],
        ["a holiday's is the day before once a later day is in", RATES, "2026-12-25", 0, RATES[3]],
        ["a weekend's after a Friday holiday waits for Monday", RATES.slice(0, 4), "2026-12-26", 0, undefined],
        ["a weekend's after a Friday holiday is Thursday's", RATES, "2026-12-26", 0, RATES[3]],
        ["two lock days count only days with a rate", RATES, "2026-12-22", 2, RATES[1]],
        ["two lock days skip the weekend", RATES, "2026-12-21", 2, RATES[0]],
        ["a lock day skips Christmas Friday", RATES, "2026-12-28", 1, RATES[3]],
        ["a lock day before Monday is Friday's", RATES.slice(0, 2), "2026-12-21", 1, RATES[1]],
        ["a lock day before Monday waits for Friday's", RATES.slice(0, 1), "2026-12-21", 1, undefined],
        ["a lock day before Tuesday waits for Monday's", RATES.slice(0, 2), "2026-12-22", 1, undefined],
        ["a lock before the first rate is nothing", RATES, "2026-12-18", 2, undefined],
        ["a reset before any rate is nothing", RATES, "1998-06-01", 0, undefined],
        ["no rates are nothing", [], "2026-12-18", 0, undefined],
    ];

    it.each(cases)("%s", (_name, series, reset, lockDays, expected) => {
        expect(lockedOn(series, reset, lockDays)).toEqual(expected);
    });
});

describe("lock periods", () => {
    const year: Point[] = [
        { day: "2025-10-03", value: 2.224 },
        { day: "2026-03-13", value: 2.522 },
        { day: "2026-10-05", value: 3.186 },
        { day: "2026-11-19", value: 3.343 },
    ];

    it("run from each reset to the next, counted from the reset day entered", () => {
        // A loan reset on a Sunday 5 October 2025 locked Friday's rate. The day entered may be any reset, even a future one.
        for (const entered of ["2025-10-05", "2027-10-05", "2020-10-05"]) {
            expect(lockPeriods(year, entered, 12, 0, "2025-09-22", "2026-11-22")).toEqual([
                { reset: "2025-10-05", until: "2026-10-05", locked: year[0] },
                { reset: "2026-10-05", until: "2027-10-05", locked: year[2] },
            ]);
        }
        expect(lockPeriods(year, "2025-10-05", 12, 0, "2026-01-01", "2026-11-22")).toHaveLength(2);
    });

    it("leave out a reset before the statistics begin", () => {
        expect(lockPeriods(year.slice(1), "2025-10-05", 12, 0, "2025-09-22", "2026-11-22")).toEqual([
            { reset: "2026-10-05", until: "2027-10-05", locked: year[2] },
        ]);
    });

    it("take a reset before the statistics from the integration, when it gives that reset's rate", () => {
        // The statistics begin after the reset of 5 October 2025, which the loan's sensor says locked 2.224.
        const known = { reset: "2025-10-05", locked: year[0] };
        expect(lockPeriods(year.slice(1), "2025-10-05", 12, 0, "2025-11-22", "2026-11-22", known)).toEqual([
            { reset: "2025-10-05", until: "2026-10-05", locked: year[0] },
            { reset: "2026-10-05", until: "2027-10-05", locked: year[2] },
        ]);
        // A rate given for another reset is left alone.
        const other = { ...known, reset: "2024-10-05" };
        expect(lockPeriods(year.slice(1), "2025-10-05", 12, 0, "2025-11-22", "2026-11-22", other)).toHaveLength(1);
    });

    it("leave out a reset whose rate isn't out yet", () => {
        const waiting = year.slice(0, 2);
        expect(lockPeriods(waiting, "2025-10-05", 12, 0, "2025-09-22", "2026-10-05")).toEqual([
            { reset: "2025-10-05", until: "2026-10-05", locked: year[0] },
        ]);
    });

    it("include a weekend reset as soon as Friday's rate is out, as the integration does", () => {
        // Saturday 19 December locks Friday 18 December's rate, which is the newest in the statistics.
        expect(lockPeriods(RATES.slice(0, 2), "2026-12-19", 12, 0, "2026-12-01", "2026-12-19")).toEqual([
            { reset: "2026-12-19", until: "2027-12-19", locked: RATES[1] },
        ]);
    });

    it("include a reset locked a day before on the reset day itself", () => {
        // With one lock day, Tuesday 22 December locks Monday's rate, which is out on Tuesday.
        expect(lockPeriods(RATES.slice(0, 3), "2026-12-22", 1, 1, "2026-12-01", "2026-12-22")).toEqual([
            { reset: "2026-12-22", until: "2027-01-22", locked: RATES[2] },
        ]);
    });

    it("return to the 31st after a shorter month", () => {
        const rates: Point[] = [
            { day: "2026-01-30", value: 2.1 },
            { day: "2026-02-27", value: 2.2 },
            { day: "2026-03-31", value: 2.3 },
            { day: "2026-04-01", value: 2.4 },
        ];
        const periods = lockPeriods(rates, "2026-01-31", 1, 0, "2026-01-15", "2026-04-01");
        expect(periods.map(({ reset, until }) => [reset, until])).toEqual([
            ["2026-01-31", "2026-02-28"],
            ["2026-02-28", "2026-03-31"],
            ["2026-03-31", "2026-04-30"],
        ]);
        expect(periods.map(({ locked }) => locked.value)).toEqual([2.1, 2.2, 2.3]);
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
