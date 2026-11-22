/**
 * The Euribor card: a maturity's newest rate and its history, the ECB's deposit facility rate on the same chart, and the
 * loans that follow the maturity. Its layout follows the number of loans: none, the rate and the chart; one or two, a
 * tile per loan over the chart; three or more, the rate and the chart over a table of the loans.
 *
 * The card is as tall as the rows it is given. Everything but the chart keeps to lines that never wrap, and the chart
 * takes what is left, so the height never depends on the data.
 */
import { LitElement, css, html, nothing } from "lit";
import type { PropertyValues, TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { chart, scale } from "./chart";
import type { ChartInput, ChartLoan } from "./chart";
import { CARD_VERSION, DEFAULT_ROWS, LOAN_COLORS, ROW_GAP, ROW_HEIGHT, STALE_HOURS, minimumRows } from "./const";
import { MONTHS_BY_MATURITY, rateSensors, sources } from "./data";
import type { Loan, Sources } from "./data";
import "./editor";
import type { HomeAssistant } from "./hass";
import { browserLanguage, translate } from "./localize/localize";
import { availableRanges, changes, lockPeriods, points, rangeStart } from "./series";
import type { Point, RangeKey, StatisticRow } from "./series";
import type { EuriborCardConfig } from "./types";

interface CardRegistration {
    type: string;
    name: string;
    description: string;
    documentationURL: string;
    preview: boolean;
}

interface Statistics {
    key: string;
    rates: Point[];
    ecb: Point[];
    /** Whether the newest rows are the days the history sensors show. */
    complete: boolean;
    readAt: number;
    retries: number;
}

// The statistics are read from the start of Euribor, as the ranges shown depend on how far back they reach.
const HISTORY_START = "1998-12-30T00:00:00Z";
// A failed read, or one that came before the recorder had written the newest day, is tried again after a minute, the
// latter a few times at most.
const RETRY_MS = 60_000;
const MAX_RETRIES = 5;

export class EuriborCard extends LitElement {
    @property({ attribute: false }) public hass?: HomeAssistant;
    @property({ attribute: false }) public layout?: string;
    @state() private config?: EuriborCardConfig;
    @state() private statistics?: Statistics;
    @state() private range?: RangeKey;
    @state() private hover?: string;
    @state() private size = { width: 0, height: 0 };
    private loading?: string;
    private failed?: { key: string; at: number };
    private observer?: ResizeObserver;

    public static getConfigElement(): HTMLElement {
        return document.createElement("euribor-card-editor");
    }

    public static getStubConfig(hass?: HomeAssistant): Record<string, unknown> {
        return { entity: hass ? (rateSensors(hass)[0] ?? "") : "" };
    }

    public setConfig(config: EuriborCardConfig): void {
        if (!config) {
            throw new Error("Invalid configuration");
        }
        this.config = { ...config };
    }

    public getGridOptions(): Record<string, unknown> {
        return { columns: 12, min_columns: 12, rows: DEFAULT_ROWS, min_rows: minimumRows(this.sources()?.loans.length ?? 0) };
    }

    public getCardSize(): number {
        return DEFAULT_ROWS;
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        this.observer?.disconnect();
        this.observer = undefined;
    }

    protected updated(changed: PropertyValues): void {
        super.updated(changed);
        this.observeChart();
        if (changed.has("hass") || changed.has("config")) {
            void this.loadStatistics();
        }
    }

    protected render(): TemplateResult {
        const found = this.sources();
        const outside = this.layout !== "grid" ? `height: ${DEFAULT_ROWS * ROW_HEIGHT + (DEFAULT_ROWS - 1) * ROW_GAP}px` : "";
        if (!this.config?.entity || !found) {
            return html`<ha-card style=${outside}
                ><div class="message">${this.text(this.config?.entity ? "card.unavailable" : "card.no_entity")}</div></ha-card
            >`;
        }
        const loans = found.loans;
        const body = !loans.length ? this.layoutRate(found) : loans.length <= 2 ? this.layoutTiles(found) : this.layoutTable(found);
        return html`<ha-card style=${outside}>${body}</ha-card>`;
    }

    /** No loans: the rate in the header, its changes, the chart. */
    private layoutRate(found: Sources): TemplateResult {
        return html`${this.header(found)}${this.changeChips(false)}${this.chartBox(found, [])}${this.legend(found, false)}`;
    }

    /** One or two loans: a tile each, then the rate on one line and the chart. */
    private layoutTiles(found: Sources): TemplateResult {
        const one = found.loans.length === 1;
        const tiles = found.loans.map((loan, index) => {
            const change = loan.change;
            // Two tiles on a narrow card have room for the shortest notice only.
            const next = loan.pending
                ? html`<span class="pending"
                      ><ha-icon icon="mdi:timer-sand"></ha-icon
                      ><span class=${one ? "" : "pending-wide"}>${this.text(one ? "card.pending_long" : "card.pending_short")}</span
                      >${one ? nothing : html`<span class="pending-narrow">${this.text("card.pending_tiny")}</span>`}</span
                  >`
                : html`${one ? `${this.text("card.next")} ` : ""}<b class=${this.tone(change, true)}>${this.signed(change, 3)}</b> →
                      ${this.percent(loan.rateToday, 3)}`;
            const locked =
                one && loan.locked !== undefined
                    ? ` · ${this.text("card.locked_line").replace("{rate}", this.number(loan.locked, 3)).replace("{margin}", this.number(loan.margin, 2))}`
                    : "";
            return html`<div class="tile">
                <div class="tile-name line" title=${loan.name}>
                    <span class="dot" style="background: ${LOAN_COLORS[index % LOAN_COLORS.length]}"></span>${loan.name}
                </div>
                <div class="tile-rate">${this.percent(loan.rate, 3)}</div>
                <div class="tile-line line">${next}</div>
                <div class="tile-line line">${this.resetLine(loan)}${locked}</div>
            </div>`;
        });
        return html`<div class="tiles" style="grid-template-columns: repeat(${found.loans.length}, minmax(0, 1fr))">${tiles}</div>
            <div class="rate-line">
                <div class="line">
                    <span class="title">${this.cardTitle(found)}</span>
                    <span class="rate-small ${this.stale(found) ? "stale" : ""}">${this.percent(Number(found.rate.state), 3)}</span>
                </div>
                ${this.ranges()}
            </div>
            ${this.published(found)}${this.chartBox(found, found.loans)}${this.legend(found, this.loanMarks() === "lines")}`;
    }

    /** Three or more loans: the header and the chart, then a line per loan. */
    private layoutTable(found: Sources): TemplateResult {
        const rows = found.loans.map((loan, index) => {
            const next = loan.pending
                ? html`<span class="pending"><ha-icon icon="mdi:timer-sand"></ha-icon>${this.text("card.pending_tiny")}</span>`
                : html`<b>${this.percent(loan.rateToday, 2)}</b>
                      <span class=${this.tone(loan.change, true)}>${this.signed(loan.change, 2)}</span>`;
            return html`<div class="loan-row">
                <span class="loan-name"
                    ><span class="dot" style="background: ${LOAN_COLORS[index % LOAN_COLORS.length]}"></span
                    ><span class="line">${loan.name}</span></span
                >
                <span class="loan-now">${this.percent(loan.rate, 2)}</span>
                <span class="loan-next">${next} · ${loan.nextReset ? this.shortDate(loan.nextReset) : ""}</span>
            </div>`;
        });
        return html`${this.header(found)}${this.changeChips(true)}${this.chartBox(found, found.loans)}${this.legend(found, this.loanMarks() === "lines")}
            <div class="loans">
                <div class="loan-row loan-head">
                    <span></span><span>${this.text("card.now")}</span><span>${this.text("card.at_reset")}</span>
                </div>
                ${rows}
            </div>`;
    }

    private header(found: Sources): TemplateResult {
        return html`<div class="header">
                <div class="header-text">
                    <div class="title line">${this.cardTitle(found)}</div>
                    <div class="rate-big ${this.stale(found) ? "stale" : ""}">
                        ${this.number(Number(found.rate.state), 3)}<small> %</small>
                    </div>
                </div>
                ${this.ranges()}
            </div>
            ${this.published(found)}`;
    }

    private published(found: Sources): TemplateResult {
        const hours = this.ageHours(found);
        if (hours !== undefined && hours > STALE_HOURS) {
            return html`<div class="published stale-text line">
                <ha-icon icon="mdi:clock-alert-outline"></ha-icon
                >${this.text("card.stale").replace("{days}", String(Math.floor(hours / 24)))}
            </div>`;
        }
        const day = found.rate.attributes.latest_date;
        const at = found.published?.state ? new Date(found.published.state) : undefined;
        const when = at && !Number.isNaN(at.getTime()) ? this.dateTime(at) : "";
        return html`<div class="published line">
            ${typeof day === "string" ? this.text("card.published").replace("{date}", this.shortDate(day)).replace("{published}", when) : ""}
        </div>`;
    }

    private changeChips(loans: boolean): TemplateResult {
        const { month, year } = changes(this.statistics?.rates ?? []);
        const chip = (label: string, value: number | undefined) =>
            value === undefined ? nothing : html`<span class="chip ${this.tone(value, loans)}">${label} ${this.signed(value, 3)}</span>`;
        return html`<div class="chips">${chip(this.text("card.month"), month)}${chip(this.text("card.year"), year)}</div>`;
    }

    private ranges(): TemplateResult | typeof nothing {
        const available = this.availableRanges();
        if (available.length < 2) {
            return nothing;
        }
        const current = this.currentRange();
        return html`<div class="ranges">
                ${available.map(
                    (key) =>
                        html`<button class=${key === current ? "on" : ""} @click=${() => (this.range = key)}>
                            ${this.text(`ranges.${key}`)}
                        </button>`,
                )}
            </div>
            <select
                class="range-select"
                aria-label=${this.text("card.range")}
                @change=${(event: Event) => (this.range = (event.target as HTMLSelectElement).value as RangeKey)}
            >
                ${available.map((key) => html`<option value=${key} ?selected=${key === current}>${this.text(`ranges.${key}`)}</option>`)}
            </select>`;
    }

    private chartBox(found: Sources, loans: Loan[]): TemplateResult {
        const input = this.chartInput(found, loans);
        const point = this.hover && input ? input.rates.find((rate) => rate.day === this.hover) : undefined;
        const ecb =
            point && found.ecbRate && this.ecbMode() !== "none"
                ? this.statistics?.ecb.filter((rate) => rate.day <= point.day).at(-1)
                : undefined;
        return html`<div class="chart" @pointermove=${this.pointerMove} @pointerleave=${() => (this.hover = undefined)}>
            ${
                point
                    ? html`<div class="readout">
                          ${this.shortDate(point.day, true)} ·
                          <b>${this.percent(point.value, 3)}</b
                          >${ecb ? html` · ${this.text("card.ecb_short")} ${this.percent(ecb.value, 2)}` : nothing}
                      </div>`
                    : nothing
            }
            ${input ? chart(input) : nothing}
        </div>`;
    }

    private chartInput(found: Sources, loans: Loan[]): ChartInput | undefined {
        const rates = this.statistics?.rates ?? [];
        if (!this.size.width || !this.size.height || !rates.length) {
            return undefined;
        }
        const today = this.today();
        const start = rangeStart(this.currentRange(), rates, today);
        const months = MONTHS_BY_MATURITY[found.maturity] ?? 12;
        // The ECB's rate from the range on, with the day before it, so a step on the first day still shows as a step.
        const ecbAll = found.ecbRate ? (this.statistics?.ecb ?? []) : [];
        const ecbBefore = ecbAll.filter((point) => point.day < start).at(-1);
        const ecb = [...(ecbBefore ? [ecbBefore] : []), ...ecbAll.filter((point) => point.day >= start)];
        const chartLoans: ChartLoan[] = loans.map((loan, index) => ({
            color: LOAN_COLORS[index % LOAN_COLORS.length],
            periods: loan.enteredReset ? lockPeriods(rates, loan.enteredReset, months, loan.lockDays, start, today, loan.previous) : [],
        }));
        return {
            width: this.size.width,
            height: this.size.height,
            start,
            today,
            rates: rates.filter((point) => point.day >= start),
            ecb,
            ecbMode: this.ecbMode(),
            loans: chartLoans,
            loanMarks: loans.length ? this.loanMarks() : "none",
            hover: this.hover,
            number: (value, digits) => this.number(value, digits),
            month: (day) => this.monthLabel(day),
            date: (day) => this.shortDate(day, true),
        };
    }

    // The rate's own line needs no entry, as the title above it names it in the same colour.
    private legend(found: Sources, locked: boolean): TemplateResult | typeof nothing {
        const ecb = !!found.ecbRate && this.ecbMode() === "steps";
        if (!locked && !ecb) {
            return nothing;
        }
        return html`<div class="legend">
            ${locked ? html`<span><i class="swatch lock-swatch"></i>${this.text("card.locked_legend")}</span>` : nothing}
            ${ecb ? html`<span><i class="swatch ecb-swatch"></i>${this.text("card.ecb_legend")}</span>` : nothing}
        </div>`;
    }

    private pointerMove(event: PointerEvent): void {
        const found = this.sources();
        const svg = (event.currentTarget as HTMLElement).querySelector("svg");
        const input = found ? this.chartInput(found, found.loans) : undefined;
        if (!svg || !input) {
            return;
        }
        const box = svg.getBoundingClientRect();
        const day = scale(input).dayAt(((event.clientX - box.left) / box.width) * input.width);
        const point = input.rates.reduce<Point | undefined>(
            (best, rate) =>
                !best || Math.abs(Date.parse(rate.day) - Date.parse(day)) < Math.abs(Date.parse(best.day) - Date.parse(day)) ? rate : best,
            undefined,
        );
        this.hover = point?.day;
    }

    private resetLine(loan: Loan): string {
        if (!loan.nextReset) {
            return "";
        }
        const days = Math.round((Date.parse(loan.nextReset) - Date.parse(this.today())) / 86_400_000);
        return `${this.shortDate(loan.nextReset, true)} · ${this.text("card.days").replace("{days}", String(days))}`;
    }

    private observeChart(): void {
        const box = this.renderRoot.querySelector<HTMLElement>(".chart");
        if (!box) {
            return;
        }
        if (!this.observer) {
            this.observer = new ResizeObserver(() => this.measureChart());
        }
        this.observer.disconnect();
        this.observer.observe(box);
        this.measureChart();
    }

    private measureChart(): void {
        const box = this.renderRoot.querySelector<HTMLElement>(".chart");
        if (!box) {
            return;
        }
        const width = Math.floor(box.clientWidth);
        const height = Math.floor(box.clientHeight);
        if (width !== this.size.width || height !== this.size.height) {
            this.size = { width, height };
        }
    }

    private async loadStatistics(): Promise<void> {
        const found = this.sources();
        if (!this.hass?.callWS || !found?.history) {
            return;
        }
        const ids = [found.history, ...(found.ecbHistory ? [found.ecbHistory] : [])];
        // A history sensor's state is the day of its newest rate, so a new day reads the statistics again.
        const key = ids.map((id) => `${id}:${this.hass?.states[id]?.state}`).join("|");
        const now = Date.now();
        const read = this.statistics?.key === key ? this.statistics : undefined;
        if (
            this.loading === key ||
            (read && (read.complete || read.retries >= MAX_RETRIES || now - read.readAt < RETRY_MS)) ||
            (this.failed?.key === key && now - this.failed.at < RETRY_MS)
        ) {
            return;
        }
        this.loading = key;
        try {
            const rows = await this.hass.callWS<Record<string, StatisticRow[]>>({
                type: "recorder/statistics_during_period",
                start_time: HISTORY_START,
                statistic_ids: ids,
                period: "day",
                types: ["mean"],
            });
            const zone = this.hass.config?.time_zone;
            const rates = points(rows[found.history], zone);
            const ecb = found.ecbHistory ? points(rows[found.ecbHistory], zone) : [];
            // The history sensor shows a new day as soon as its rows are queued, which can be before the recorder writes them.
            const newest = (series: Point[], id?: string): boolean => !id || series.at(-1)?.day === this.hass?.states[id]?.state;
            this.statistics = {
                key,
                rates,
                ecb,
                complete: newest(rates, found.history) && newest(ecb, found.ecbHistory),
                readAt: now,
                retries: read ? read.retries + 1 : 0,
            };
            this.failed = undefined;
        } catch (error) {
            this.failed = { key, at: now };
            console.error("euribor-card: the statistics couldn't be read", error);
        } finally {
            this.loading = undefined;
        }
    }

    private sources(): Sources | undefined {
        return this.hass && this.config?.entity ? sources(this.hass, this.config.entity) : undefined;
    }

    private availableRanges(): RangeKey[] {
        return availableRanges(this.statistics?.rates ?? [], this.today());
    }

    private currentRange(): RangeKey {
        const available = this.availableRanges();
        if (this.range && available.includes(this.range)) {
            return this.range;
        }
        return available.includes("1y") ? "1y" : "all";
    }

    private loanMarks() {
        return this.config?.loans_on_chart ?? "lines";
    }

    private ecbMode() {
        return this.config?.ecb ?? "steps";
    }

    private ageHours(found: Sources): number | undefined {
        const at = found.published?.state ? Date.parse(found.published.state) : NaN;
        return Number.isNaN(at) ? undefined : (Date.now() - at) / 3_600_000;
    }

    private stale(found: Sources): boolean {
        return (this.ageHours(found) ?? 0) > STALE_HOURS;
    }

    /** Red for a rise and green for a fall where loans show, as a borrower sees them, and neutral otherwise. */
    private tone(value: number | undefined, loans: boolean): string {
        if (!loans || value === undefined || value === 0) {
            return "";
        }
        return value > 0 ? "up" : "down";
    }

    private cardTitle(found: Sources): string {
        return this.hass?.formatEntityName?.(found.rate, [{ type: "device" }]) || String(found.rate.attributes.friendly_name ?? "Euribor");
    }

    private today(): string {
        return new Intl.DateTimeFormat("en-CA", {
            timeZone: this.hass?.config?.time_zone,
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
        }).format(new Date());
    }

    private number(value: number, digits: number): string {
        return new Intl.NumberFormat(this.language(), { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value);
    }

    private percent(value: number | undefined, digits: number): string {
        return value === undefined || Number.isNaN(value) ? "–" : `${this.number(value, digits)} %`;
    }

    private signed(value: number | undefined, digits: number): string {
        if (value === undefined) {
            return "–";
        }
        return `${value > 0 ? "+" : value < 0 ? "−" : "±"}${this.number(Math.abs(value), digits)}`;
    }

    private shortDate(day: string, year = false): string {
        const options: Intl.DateTimeFormatOptions = year
            ? { day: "numeric", month: "numeric", year: "numeric" }
            : { day: "numeric", month: "numeric" };
        return new Intl.DateTimeFormat(this.language(), { ...options, timeZone: "UTC" }).format(new Date(`${day}T12:00:00Z`));
    }

    private dateTime(at: Date): string {
        return new Intl.DateTimeFormat(this.language(), {
            day: "numeric",
            month: "numeric",
            hour: "numeric",
            minute: "2-digit",
            timeZone: this.hass?.config?.time_zone,
        }).format(at);
    }

    private monthLabel(day: string): string {
        const date = new Date(`${day}T12:00:00Z`);
        const span = this.currentRange() === "1m";
        if (span) {
            return this.shortDate(day);
        }
        const month = new Intl.DateTimeFormat(this.language(), { month: "short", timeZone: "UTC" }).format(date).replace(".", "");
        return date.getUTCMonth() === 0 ? `${month} ${String(date.getUTCFullYear()).slice(2)}` : month;
    }

    private text(key: string): string {
        return translate(this.language(), key);
    }

    private language(): string {
        return this.hass?.locale?.language ?? this.hass?.language ?? browserLanguage();
    }

    static styles = css`
        :host {
            --euribor-card-rate: var(--primary-color);
            --euribor-card-ecb: var(--purple-color, #926bc7);
        }
        ha-card {
            box-sizing: border-box;
            height: 100%;
            padding: 16px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            container-type: inline-size;
        }
        .message {
            color: var(--secondary-text-color);
        }
        .line {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            min-width: 0;
        }
        .header,
        .rate-line {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 8px;
            flex: none;
        }
        .rate-line {
            align-items: baseline;
            margin-top: 12px;
        }
        .header-text {
            min-width: 0;
        }
        .title {
            color: var(--secondary-text-color);
            font-size: 14px;
        }
        .rate-big {
            font-size: 28px;
            font-weight: 600;
            line-height: 1.15;
            color: var(--euribor-card-rate);
        }
        .rate-big small {
            font-size: 15px;
            font-weight: 500;
        }
        .rate-small {
            font-size: 16px;
            font-weight: 600;
            color: var(--euribor-card-rate);
        }
        .stale {
            color: var(--secondary-text-color);
        }
        .published {
            flex: none;
            font-size: 12px;
            color: var(--secondary-text-color);
        }
        .stale-text {
            color: var(--warning-color);
        }
        .published ha-icon,
        .pending ha-icon {
            --mdc-icon-size: 14px;
            vertical-align: -2px;
            margin-right: 2px;
        }
        .chips {
            display: flex;
            gap: 6px;
            margin-top: 6px;
            flex: none;
            min-height: 20px;
        }
        .chip {
            font-size: 12px;
            line-height: 18px;
            padding: 0 7px;
            border-radius: 999px;
            background: rgba(127, 127, 127, 0.12);
            color: var(--secondary-text-color);
            white-space: nowrap;
        }
        .up {
            color: var(--error-color);
        }
        .down {
            color: var(--success-color);
        }
        .chip.up {
            background: color-mix(in srgb, var(--error-color) 12%, transparent);
        }
        .chip.down {
            background: color-mix(in srgb, var(--success-color) 12%, transparent);
        }
        .pending {
            color: var(--warning-color);
        }
        .ranges {
            display: flex;
            gap: 2px;
            flex: none;
        }
        .ranges button {
            background: transparent;
            border: 0;
            color: var(--secondary-text-color);
            font: inherit;
            font-size: 12px;
            padding: 3px 7px;
            border-radius: 8px;
            cursor: pointer;
        }
        .ranges button.on {
            background: color-mix(in srgb, var(--primary-color) 15%, transparent);
            color: var(--primary-color);
        }
        .range-select {
            display: none;
            flex: none;
            font: inherit;
            font-size: 12px;
            color: var(--primary-color);
            background: transparent;
            border: 1px solid var(--divider-color);
            border-radius: 8px;
            padding: 2px 4px;
        }
        /* Below 394 px of card the six range buttons don't fit beside the title, so they turn into a list. */
        .pending-narrow {
            display: none;
        }
        @container (max-width: 360px) {
            .ranges,
            .pending-wide {
                display: none;
            }
            .pending-narrow {
                display: inline;
            }
            .range-select {
                display: block;
            }
        }
        .chart {
            flex: 1 1 0;
            min-height: 0;
            margin: 8px -4px 0;
            position: relative;
            touch-action: pan-y;
        }
        .chart svg {
            display: block;
            position: absolute;
            inset: 0;
        }
        .readout {
            position: absolute;
            top: 0;
            left: 4px;
            z-index: 1;
            font-size: 12px;
            padding: 1px 6px;
            border-radius: 6px;
            background: var(--card-background-color);
            pointer-events: none;
            white-space: nowrap;
        }
        .grid {
            stroke: var(--divider-color);
            stroke-width: 1;
        }
        .axis {
            fill: var(--secondary-text-color);
            font-size: 10px;
        }
        .rate {
            fill: none;
            stroke: var(--euribor-card-rate);
            stroke-width: 1.6;
            stroke-linejoin: round;
        }
        .ecb-step {
            fill: none;
            stroke: var(--euribor-card-ecb);
            stroke-width: 1.5;
            stroke-dasharray: 4 3;
        }
        .ecb {
            fill: var(--euribor-card-ecb);
        }
        .ecb-mark {
            stroke: var(--euribor-card-ecb);
            opacity: 0.35;
        }
        .ecb-label {
            fill: var(--euribor-card-ecb);
            font-size: 9px;
        }
        .lock {
            stroke-width: 3;
            stroke-linecap: round;
            opacity: 0.6;
        }
        .marker {
            fill: var(--card-background-color);
            stroke-width: 2;
        }
        .hover {
            stroke: var(--secondary-text-color);
            opacity: 0.6;
        }
        .hover-dot {
            fill: var(--euribor-card-rate);
        }
        .legend {
            display: flex;
            gap: 12px;
            margin-top: 4px;
            flex: none;
            font-size: 11px;
            color: var(--secondary-text-color);
            white-space: nowrap;
            overflow: hidden;
        }
        .swatch {
            display: inline-block;
            width: 12px;
            height: 2px;
            vertical-align: middle;
            margin-right: 4px;
        }
        .lock-swatch {
            height: 3px;
            background: var(--secondary-text-color);
        }
        .ecb-swatch {
            background: var(--euribor-card-ecb);
        }
        .dot {
            display: inline-block;
            flex: none;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 6px;
        }
        .tiles {
            display: grid;
            gap: 10px;
            flex: none;
        }
        .tile {
            min-width: 0;
            padding: 10px 12px;
            border-radius: 12px;
            border: 1px solid var(--divider-color);
        }
        .tile-name {
            font-size: 13px;
            color: var(--secondary-text-color);
        }
        .tile-rate {
            font-size: 24px;
            font-weight: 600;
            margin: 1px 0;
        }
        .tile-line {
            font-size: 12px;
            line-height: 1.55;
            color: var(--secondary-text-color);
        }
        .tile-line b {
            font-weight: 600;
        }
        .loans {
            flex: none;
            margin-top: 8px;
            padding-top: 6px;
            border-top: 1px solid var(--divider-color);
        }
        .loan-row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto auto;
            gap: 10px;
            align-items: baseline;
            font-size: 13px;
            line-height: 24px;
        }
        .loan-head {
            font-size: 11px;
            line-height: 16px;
            color: var(--secondary-text-color);
        }
        .loan-head span:not(:first-child),
        .loan-now,
        .loan-next {
            text-align: right;
        }
        .loan-name {
            display: flex;
            align-items: center;
            min-width: 0;
        }
        .loan-now {
            font-weight: 600;
        }
        .loan-next {
            font-size: 12px;
            color: var(--secondary-text-color);
            white-space: nowrap;
        }
        .loan-next b {
            color: var(--primary-text-color);
            font-weight: 600;
        }
    `;
}

if (!customElements.get("euribor-card")) {
    console.info(
        `%c  EURIBOR-CARD \n%c  ${CARD_VERSION}    `,
        "color: orange; font-weight: bold; background: black",
        "color: white; font-weight: bold; background: dimgray",
    );

    const registry = window as unknown as { customCards?: CardRegistration[] };
    registry.customCards = registry.customCards ?? [];
    registry.customCards.push({
        type: "euribor-card",
        name: translate(browserLanguage(), "common.name"),
        description: translate(browserLanguage(), "common.description"),
        documentationURL: "https://github.com/jesmak/euribor_rates#euribor-card",
        preview: true,
    });
    customElements.define("euribor-card", EuriborCard);
}

declare global {
    interface HTMLElementTagNameMap {
        "euribor-card": EuriborCard;
    }
}
