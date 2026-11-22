/** The card's visual editor: the maturity, the loans shown and how, the ECB's rate and the range. */
import { LitElement, html, nothing } from "lit";
import type { TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { rateSensors, sources } from "./data";
import type { HomeAssistant } from "./hass";
import { browserLanguage, translate } from "./localize/localize";
import { RANGES } from "./series";
import type { EuriborCardConfig } from "./types";

type LoanMode = "all" | "chosen" | "none";

interface SchemaEntry {
    name: string;
}

const DEFAULTS: Record<string, unknown> = {
    loans_on_chart: "lines",
    ecb: "steps",
    show_ranges: true,
    range: "1y",
};

function schema(hass: HomeAssistant, config: EuriborCardConfig, mode: LoanMode, text: (key: string) => string) {
    const select = (options: [string, string][]) => ({
        select: { mode: "dropdown", options: options.map(([value, label]) => ({ value, label: text(`editor.${label}`) })) },
    });
    return [
        { name: "entity", required: true, selector: { entity: { include_entities: rateSensors(hass) } } },
        {
            name: "loan_mode",
            selector: select([
                ["all", "loans_all"],
                ["chosen", "loans_chosen"],
                ["none", "none"],
            ]),
        },
        ...(mode === "chosen"
            ? [
                  {
                      name: "loans",
                      selector: {
                          entity: {
                              multiple: true,
                              include_entities:
                                  (config.entity ? sources(hass, config.entity)?.loans : undefined)?.map((loan) => loan.entity) ?? [],
                          },
                      },
                  },
              ]
            : []),
        {
            name: "loans_on_chart",
            selector: select([
                ["markers", "markers"],
                ["lines", "lines"],
                ["none", "none"],
            ]),
        },
        {
            name: "ecb",
            selector: select([
                ["steps", "steps"],
                ["markers", "axis_markers"],
                ["none", "none"],
            ]),
        },
        { name: "show_ranges", selector: { boolean: {} } },
        {
            name: "range",
            selector: { select: { mode: "dropdown", options: RANGES.map(({ key }) => ({ value: key, label: text(`ranges.${key}`) })) } },
        },
    ];
}

export class EuriborCardEditor extends LitElement {
    @property({ attribute: false }) public hass?: HomeAssistant;
    @state() private config: EuriborCardConfig = { type: "custom:euribor-card", entity: "" };
    // Kept apart from the configuration, as chosen loans with none picked yet are an empty list just like no loans.
    @state() private loanMode: LoanMode = "all";

    public setConfig(config: EuriborCardConfig): void {
        this.config = { ...config };
        if (!Array.isArray(config.loans)) {
            this.loanMode = "all";
        } else if (config.loans.length) {
            this.loanMode = "chosen";
        } else if (this.loanMode !== "chosen") {
            this.loanMode = "none";
        }
    }

    protected render(): TemplateResult | typeof nothing {
        if (!this.hass) {
            return nothing;
        }
        return html`
            <ha-form
                .hass=${this.hass}
                .data=${{ ...DEFAULTS, ...this.config, loan_mode: this.loanMode }}
                .schema=${schema(this.hass, this.config, this.loanMode, (key) => this.text(key))}
                .computeLabel=${(entry: SchemaEntry) => this.text(`editor.${entry.name}`)}
                .computeHelper=${(entry: SchemaEntry) => this.helper(entry.name)}
                @value-changed=${this.valueChanged}
            ></ha-form>
        `;
    }

    private valueChanged(event: CustomEvent<{ value: EuriborCardConfig & { loan_mode?: LoanMode } }>): void {
        const { loan_mode: mode = "all", ...value } = event.detail.value;
        // The form's values with the configuration's keys in their order, so the YAML doesn't reshuffle at every change.
        const order = [...Object.keys(this.config).filter((key) => key in value), ...Object.keys(value)];
        const config = Object.fromEntries(order.map((key) => [key, (value as Record<string, unknown>)[key]])) as EuriborCardConfig;
        this.loanMode = mode;
        if (mode === "all") {
            delete config.loans;
        } else if (mode === "none" || !Array.isArray(config.loans)) {
            config.loans = [];
        }
        // The defaults are shown in the form but left out of the configuration.
        for (const [key, value] of Object.entries(DEFAULTS)) {
            if (config[key] === value || config[key] === undefined || config[key] === null) {
                delete config[key];
            }
        }
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
    }

    private text(key: string): string {
        return translate(this.language(), key);
    }

    private helper(name: string): string | undefined {
        const key = `editor.${name}_helper`;
        const helper = translate(this.language(), key);
        return helper === key ? undefined : helper;
    }

    private language(): string {
        return this.hass?.locale?.language ?? this.hass?.language ?? browserLanguage();
    }
}

if (!customElements.get("euribor-card-editor")) {
    customElements.define("euribor-card-editor", EuriborCardEditor);
}

declare global {
    interface HTMLElementTagNameMap {
        "euribor-card-editor": EuriborCardEditor;
    }
}
