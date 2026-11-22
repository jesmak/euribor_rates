import type { EcbMode, LoanMarks } from "./chart";
import type { LovelaceCardConfig } from "./hass";
import type { RangeKey } from "./series";

export interface EuriborCardConfig extends LovelaceCardConfig {
    /** A maturity's rate sensor. */
    entity: string;
    /** The loans shown, in this order. Every loan that follows the maturity unless set, none when empty. */
    loans?: string[];
    /** How the loans' locked rates show on the chart. Lines unless set. */
    loans_on_chart?: LoanMarks;
    /** How the ECB's deposit facility rate shows on the chart, when the integration follows it. Steps unless set. */
    ecb?: EcbMode;
    /** Whether the range buttons show. They do unless set. */
    show_ranges?: boolean;
    /** The range shown first, or always when the buttons are hidden. A year unless set, all when the history is shorter. */
    range?: RangeKey;
}
