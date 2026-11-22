/** The card's visual editor: the maturity, and how the loans and the ECB's rate show on the chart. */
import { LitElement, html, nothing } from "lit";
import type { TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { rateSensors } from "./data";
import type { HomeAssistant } from "./hass";
import { browserLanguage, translate } from "./localize/localize";
import type { EuriborCardConfig } from "./types";

interface SchemaEntry {
    name: string;
}

const DEFAULTS: Record<string, unknown> = {
    loans_on_chart: "lines",
    ecb: "steps",
};

function schema(hass: HomeAssistant, text: (key: string) => string) {
    const select = (options: [string, string][]) => ({
        select: { mode: "dropdown", options: options.map(([value, label]) => ({ value, label: text(`editor.${label}`) })) },
    });
    return [
        { name: "entity", required: true, selector: { entity: { include_entities: rateSensors(hass) } } },
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
    ];
}

export class EuriborCardEditor extends LitElement {
    @property({ attribute: false }) public hass?: HomeAssistant;
    @state() private config: EuriborCardConfig = { type: "custom:euribor-card", entity: "" };

    public setConfig(config: EuriborCardConfig): void {
        this.config = { ...config };
    }

    protected render(): TemplateResult | typeof nothing {
        if (!this.hass) {
            return nothing;
        }
        return html`
            <ha-form
                .hass=${this.hass}
                .data=${{ ...DEFAULTS, ...this.config }}
                .schema=${schema(this.hass, (key) => this.text(key))}
                .computeLabel=${(entry: SchemaEntry) => this.text(`editor.${entry.name}`)}
                .computeHelper=${(entry: SchemaEntry) => this.helper(entry.name)}
                @value-changed=${this.valueChanged}
            ></ha-form>
        `;
    }

    private valueChanged(event: CustomEvent<{ value: EuriborCardConfig }>): void {
        const config: EuriborCardConfig = { ...event.detail.value };
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
