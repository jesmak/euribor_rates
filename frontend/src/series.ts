// The rates as the card works with them: one point per day from the history sensors' statistics, what is worked out
// from them (the ranges the history covers, the changes over a month and a year), and the loans' lock periods as the
// integration gives them.

/** One day's rate. `day` is the day the statistics row is for, as YYYY-MM-DD in Home Assistant's time zone. */
export interface Point {
    day: string;
    value: number;
}

export interface StatisticRow {
    start: number | string;
    mean?: number | null;
}

/** The days of the statistics rows, in the time zone Home Assistant groups them by. */
export function points(rows: StatisticRow[] | undefined, timeZone: string | undefined): Point[] {
    const format = new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" });
    const result: Point[] = [];
    for (const row of rows ?? []) {
        if (typeof row.mean !== "number") {
            continue;
        }
        result.push({ day: format.format(new Date(row.start)), value: row.mean });
    }
    return result.sort((a, b) => a.day.localeCompare(b.day));
}

/** A day as a moment, its noon in UTC, so that drawing it never lands on the day before or after. */
export function moment(day: string): number {
    return Date.parse(`${day}T12:00:00Z`);
}

export function dayOf(time: number): string {
    return new Date(time).toISOString().slice(0, 10);
}

export const DAY = 86_400_000;

/** The same day of the month, months later or earlier, or that month's last day when it is shorter, as the integration counts. */
export function addMonths(day: string, months: number): string {
    const [year, month, date] = day.split("-").map(Number);
    const total = year * 12 + (month - 1) + months;
    const newYear = Math.floor(total / 12);
    const newMonth = total - newYear * 12;
    const last = new Date(Date.UTC(newYear, newMonth + 1, 0)).getUTCDate();
    return `${String(newYear).padStart(4, "0")}-${String(newMonth + 1).padStart(2, "0")}-${String(Math.min(date, last)).padStart(2, "0")}`;
}

/** The newest point on or before a day. */
export function valueOn(series: Point[], day: string): Point | undefined {
    let found: Point | undefined;
    for (const point of series) {
        if (point.day > day) {
            break;
        }
        found = point;
    }
    return found;
}

export type RangeKey = "1m" | "1y" | "2y" | "3y" | "5y" | "all";

export const RANGES: { key: RangeKey; months: number }[] = [
    { key: "1m", months: 1 },
    { key: "1y", months: 12 },
    { key: "2y", months: 24 },
    { key: "3y", months: 36 },
    { key: "5y", months: 60 },
    { key: "all", months: 0 },
];

// The history setting counts calendar days back from today and the first of them may be a weekend, so a range counts as
// covered a few days short of its start.
const SLACK_DAYS = 7;

/** The ranges the history covers. All is always there, as the whole history. */
export function availableRanges(series: Point[], today: string): RangeKey[] {
    const first = series[0]?.day;
    if (!first) {
        return [];
    }
    return RANGES.filter(({ key, months }) => key === "all" || dayOf(moment(addMonths(today, -months)) + SLACK_DAYS * DAY) >= first).map(
        ({ key }) => key,
    );
}

/** The first day a range shows. */
export function rangeStart(range: RangeKey, series: Point[], today: string): string {
    const months = RANGES.find(({ key }) => key === range)?.months ?? 0;
    return months ? addMonths(today, -months) : (series[0]?.day ?? today);
}

/** The newest rate less the one a month and a year earlier, a change left out when the history doesn't reach that far. */
export function changes(series: Point[]): { month?: number; year?: number } {
    const newest = series.at(-1);
    if (!newest) {
        return {};
    }
    const change = (months: number): number | undefined => {
        const then = valueOn(series, addMonths(newest.day, -months));
        return then ? newest.value - then.value : undefined;
    };
    return { month: change(1), year: change(12) };
}

/** A loan's lock period: from its reset to the next, at the Euribor the reset locked. */
export interface LockPeriod {
    reset: string;
    until: string;
    locked: Point;
}

/** The lock periods in the integration's answer to `euribor_rates/loan_periods`, leaving out anything malformed. */
export function periodsFrom(result: unknown): LockPeriod[] {
    const periods = (result as { periods?: unknown } | undefined)?.periods;
    if (!Array.isArray(periods)) {
        return [];
    }
    const day = (value: unknown): value is string => typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value);
    return periods.flatMap((period: Record<string, unknown>) =>
        day(period.reset) && day(period.until) && day(period.rate_date) && typeof period.rate === "number"
            ? [{ reset: period.reset, until: period.until, locked: { day: period.rate_date, value: period.rate } }]
            : [],
    );
}

/** The days the ECB's rate changed, with the rate before and after. */
export function steps(series: Point[]): { day: string; from: number; to: number }[] {
    const result: { day: string; from: number; to: number }[] = [];
    for (let index = 1; index < series.length; index++) {
        if (series[index].value !== series[index - 1].value) {
            result.push({ day: series[index].day, from: series[index - 1].value, to: series[index].value });
        }
    }
    return result;
}
