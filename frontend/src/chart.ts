/**
 * The chart, drawn as SVG at the size it is given, in pixels, so its texts keep their size at every width and height.
 */
import { svg } from "lit";
import type { SVGTemplateResult } from "lit";

import { DAY, dayOf, moment, steps } from "./series";
import type { LockPeriod, Point } from "./series";

export type LoanMarks = "markers" | "lines" | "none";
export type EcbMode = "steps" | "markers" | "none";

export interface ChartLoan {
    color: string;
    periods: LockPeriod[];
}

export interface ChartInput {
    width: number;
    height: number;
    start: string;
    today: string;
    rates: Point[];
    ecb: Point[];
    ecbMode: EcbMode;
    loans: ChartLoan[];
    loanMarks: LoanMarks;
    hover?: string;
    /** Number and date formats, in the viewer's language. */
    number: (value: number, digits: number) => string;
    month: (day: string) => string;
    date: (day: string) => string;
}

const PAD = { left: 36, right: 8, top: 16, bottom: 16 };
export interface Scale {
    start: number;
    end: number;
    low: number;
    high: number;
    step: number;
    x(time: number): number;
    y(value: number): number;
    /** The day under a point on the chart, never after the newest rate. */
    dayAt(x: number): string;
}

export function scale(input: ChartInput): Scale {
    const start = moment(input.start);
    const end = moment(input.today);
    const values = input.rates.map((point) => point.value);
    if (input.ecbMode === "steps") {
        values.push(...input.ecb.map((point) => point.value));
    }
    if (input.loanMarks !== "none") {
        for (const loan of input.loans) {
            values.push(...loan.periods.map((period) => period.locked.value));
        }
    }
    let low = Math.min(...values);
    let high = Math.max(...values);
    if (!Number.isFinite(low)) {
        low = 0;
        high = 1;
    }
    const range = Math.max(high - low, 0.01);
    const step = range > 1 ? 0.25 : range > 0.4 ? 0.1 : range > 0.1 ? 0.05 : 0.01;
    low = Math.floor((low - range * 0.04) / step) * step;
    high = Math.ceil((high + range * 0.04) / step) * step;
    const innerWidth = Math.max(1, input.width - PAD.left - PAD.right);
    const innerHeight = Math.max(1, input.height - PAD.top - PAD.bottom);
    const newest = input.rates.at(-1)?.day ?? input.today;
    return {
        start,
        end,
        low,
        high,
        step,
        x: (time) => PAD.left + ((time - start) / (end - start)) * innerWidth,
        y: (value) => PAD.top + (1 - (value - low) / (high - low)) * innerHeight,
        dayAt: (x) => {
            const day = dayOf(start + ((x - PAD.left) / innerWidth) * (end - start));
            return day > newest ? newest : day;
        },
    };
}

/** The point nearest a day, for the hover readout. */
export function nearest(points: Point[], day: string): Point | undefined {
    const time = moment(day);
    let best: Point | undefined;
    for (const point of points) {
        if (!best || Math.abs(moment(point.day) - time) < Math.abs(moment(best.day) - time)) {
            best = point;
        }
    }
    return best;
}

export function chart(input: ChartInput): SVGTemplateResult {
    const s = scale(input);
    const { width, height } = input;
    const small = height < 110;
    const bottom = height - PAD.bottom;
    const ticks: number[] = [];
    for (let value = s.low; value <= s.high + 1e-9; value += s.step) {
        ticks.push(value);
    }
    const every = Math.ceil(ticks.length / (small ? 3 : 5));
    const digits = s.step < 0.05 ? 2 : s.step < 0.1 ? 2 : s.step < 0.25 ? 1 : 2;
    const visible = input.rates.filter((point) => moment(point.day) >= s.start);
    const line = visible
        .map((point, index) => `${index ? "L" : "M"}${s.x(moment(point.day)).toFixed(1)},${s.y(point.value).toFixed(1)}`)
        .join(" ");

    return svg`
        <svg viewBox="0 0 ${width} ${height}" width=${width} height=${height} role="img">
            ${ticks.map((value, index) =>
                index % every
                    ? null
                    : svg`<line class="grid" x1=${PAD.left} x2=${width - PAD.right} y1=${s.y(value)} y2=${s.y(value)}></line>
                          <text class="axis" x=${PAD.left - 6} y=${s.y(value) + 3} text-anchor="end">${input.number(value, digits)}</text>`,
            )}
            ${monthTicks(s, width).map((day) => svg`<text class="axis" x=${s.x(moment(day))} y=${height - 3} text-anchor="middle">${input.month(day)}</text>`)}
            ${ecb(input, s, bottom)}
            ${input.loanMarks === "lines" ? lockLines(input, s) : null}
            <path class="rate" d=${line}></path>
            ${input.loanMarks === "markers" ? lockMarkers(input, s) : null}
            ${hover(input, s, bottom)}
        </svg>
    `;
}

function monthTicks(s: Scale, width: number): string[] {
    const span = (s.end - s.start) / DAY;
    const result: string[] = [];
    if (span <= 45) {
        for (let time = s.end; time >= s.start; time -= 7 * DAY) {
            result.unshift(dayOf(time));
        }
        return result;
    }
    // About one label per 70 px, on whole months, then quarters or years when the range is long.
    const wanted = Math.max(2, Math.floor(width / 70));
    const months = [1, 2, 3, 6, 12, 24, 60].find((step) => span / 30.4 / step <= wanted) ?? 120;
    const first = new Date(s.start);
    const cursor = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth() + 1, 1, 12));
    for (; cursor.getTime() < s.end; cursor.setUTCMonth(cursor.getUTCMonth() + 1)) {
        const index = cursor.getUTCFullYear() * 12 + cursor.getUTCMonth();
        if (index % months === 0) {
            result.push(dayOf(cursor.getTime()));
        }
    }
    return result;
}

function ecb(input: ChartInput, s: Scale, bottom: number): SVGTemplateResult | null {
    if (input.ecbMode === "none" || !input.ecb.length) {
        return null;
    }
    const changes = steps(input.ecb).filter((change) => moment(change.day) >= s.start);
    if (input.ecbMode === "markers") {
        return svg`${changes.map((change) => {
            const x = s.x(moment(change.day));
            return svg`<line class="ecb-mark" x1=${x} x2=${x} y1=${PAD.top} y2=${bottom}></line>
                <path class="ecb" d="M${x - 4},${bottom} L${x + 4},${bottom} L${x},${bottom - 6} Z"></path>
                <text class="ecb-label" x=${x + 5} y=${bottom - 2}>${signed(input, change.to - change.from)}</text>`;
        })}`;
    }
    // A history shorter than the range starts the line where the history does.
    const before = input.ecb.filter((point) => moment(point.day) <= s.start).at(-1) ?? input.ecb[0];
    let path = `M${s.x(Math.max(s.start, moment(before.day)))},${s.y(before.value)}`;
    let level = before.value;
    for (const change of changes) {
        const x = s.x(moment(change.day));
        path += ` L${x},${s.y(level)} L${x},${s.y(change.to)}`;
        level = change.to;
    }
    path += ` L${s.x(s.end)},${s.y(level)}`;
    return svg`<path class="ecb-step" d=${path}></path>
        ${changes.map(
            (change) =>
                svg`<text class="ecb-label" x=${s.x(moment(change.day)) + 3} y=${s.y(change.to) - 4}>${signed(input, change.to - change.from)}</text>`,
        )}`;
}

function lockLines(input: ChartInput, s: Scale): SVGTemplateResult {
    return svg`${input.loans.map((loan) =>
        loan.periods.map((period) => {
            const from = Math.max(moment(period.reset), s.start);
            const until = Math.min(moment(period.until), s.end);
            return until > from
                ? svg`<line class="lock" style="stroke: ${loan.color}" x1=${s.x(from)} x2=${s.x(until)} y1=${s.y(period.locked.value)} y2=${s.y(period.locked.value)}></line>`
                : null;
        }),
    )}`;
}

// A marker is told apart by its loan's colour, the same as the loan's dot above the chart.
function lockMarkers(input: ChartInput, s: Scale): SVGTemplateResult {
    return svg`${input.loans.map((loan) =>
        loan.periods
            .filter((period) => moment(period.locked.day) >= s.start)
            .map((period) => {
                const x = s.x(moment(period.locked.day));
                const y = s.y(period.locked.value);
                return svg`<circle class="marker" style="stroke: ${loan.color}" cx=${x} cy=${y} r="4"></circle>`;
            }),
    )}`;
}

function hover(input: ChartInput, s: Scale, bottom: number): SVGTemplateResult | null {
    const point = input.hover ? nearest(input.rates, input.hover) : undefined;
    if (!point || moment(point.day) < s.start) {
        return null;
    }
    const x = s.x(moment(point.day));
    return svg`<line class="hover" x1=${x} x2=${x} y1=${PAD.top} y2=${bottom}></line>
        <circle class="hover-dot" cx=${x} cy=${s.y(point.value)} r="3.5"></circle>`;
}

function signed(input: ChartInput, value: number): string {
    return `${value > 0 ? "+" : value < 0 ? "−" : "±"}${input.number(Math.abs(value), 2)}`;
}
