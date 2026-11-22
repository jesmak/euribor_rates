/** Replaced at build time with the integration's version from manifest.json. */
declare const __CARD_VERSION__: string;

export const CARD_VERSION = __CARD_VERSION__;

/** The rows of a sections view the card takes unless set otherwise, and its height in pixels outside one. */
export const DEFAULT_ROWS = 7;
export const ROW_HEIGHT = 56;
export const ROW_GAP = 8;

/** The least rows without loans, with up to three, and one more for every two loans after that, so the chart stays readable. */
export function minimumRows(loans: number): number {
    return loans ? 6 + Math.max(0, Math.ceil((loans - 3) / 2)) : 4;
}

/** The loans' colours, in the order of their names. Each can be changed in a theme. */
export const LOAN_COLORS = [
    "var(--euribor-card-loan-1, var(--orange-color, #ff9800))",
    "var(--euribor-card-loan-2, var(--teal-color, #009688))",
    "var(--euribor-card-loan-3, var(--pink-color, #e91e63))",
    "var(--euribor-card-loan-4, var(--purple-color, #926bc7))",
    "var(--euribor-card-loan-5, var(--lime-color, #cddc39))",
];

/**
 * The newest rate counts as old after this long since it was published. A rate is published on the next working day,
 * so Friday's comes on Monday, and a day later after a Spanish holiday.
 */
export const STALE_HOURS = 108;
