// The rates as the card works with them: one point per day from the history sensors' statistics, and what is worked out
// from them (the ranges the history covers, the changes over a month and a year, the rate each of a loan's resets
// locked).

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

/**
 * The rate a reset locked, as the integration works it out: the reset day's own, or the last before it when the day had
 * none, or with lock days, the rate that many days with a rate before the reset day.
 */
export function lockedOn(series: Point[], reset: string, lockDays: number): Point | undefined {
    // Until the last working day it can lock is out, a missing day can't be told from one not yet published.
    const lastDay = new Date(moment(reset) - (lockDays ? DAY : 0));
    const lastWorkingDay = dayOf(lastDay.getTime() - Math.max(0, ((lastDay.getUTCDay() + 6) % 7) - 4) * DAY);
    if ((series.at(-1)?.day ?? "") < lastWorkingDay) {
        return undefined;
    }
    if (!lockDays) {
        return valueOn(series, reset);
    }
    let count = 0;
    for (let index = series.length - 1; index >= 0; index--) {
        if (series[index].day < reset && ++count === lockDays) {
            return series[index];
        }
    }
    return undefined;
}

/** A loan's lock period: from its reset to the next, at the rate the reset locked. */
export interface LockPeriod {
    reset: string;
    until: string;
    locked: Point;
}

/**
 * Every lock period that reaches into the days from `start` on, up to the reset on or before `today`. Each reset is
 * counted from the one entered for the loan, as the integration counts them, so a loan reset on the 31st returns to the
 * 31st after a shorter month. A reset whose rate the statistics don't have, being before them or not out yet, has none.
 */
export function lockPeriods(
    series: Point[],
    enteredReset: string,
    months: number,
    lockDays: number,
    start: string,
    today: string,
): LockPeriod[] {
    const monthOf = (day: string): number => Number(day.slice(0, 4)) * 12 + Number(day.slice(5, 7));
    // From a count of resets safely before the start's previous reset, as a period begun then reaches into the range.
    let count = Math.floor((monthOf(start) - monthOf(enteredReset)) / months) - 2;
    const first = series[0]?.day;
    const periods: LockPeriod[] = [];
    for (let reset = addMonths(enteredReset, count * months); reset <= today; reset = addMonths(enteredReset, ++count * months)) {
        const until = addMonths(enteredReset, (count + 1) * months);
        const locked = first && reset >= first ? lockedOn(series, reset, lockDays) : undefined;
        if (locked && until > start) {
            periods.push({ reset, until, locked });
        }
    }
    return periods;
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
