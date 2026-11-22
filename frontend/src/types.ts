import type { EcbMode, LoanMarks } from "./chart";
import type { LovelaceCardConfig } from "./hass";

export interface EuriborCardConfig extends LovelaceCardConfig {
    /** A maturity's rate sensor. */
    entity: string;
    /** How the loans' locked rates show on the chart. Lines unless set. */
    loans_on_chart?: LoanMarks;
    /** Today's rate drawn on into the future. On unless false. */
    projection?: boolean;
    /** How the ECB's deposit facility rate shows on the chart, when the integration follows it. Steps unless set. */
    ecb?: EcbMode;
}
