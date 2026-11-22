/**
 * What the card shows, found from the maturity's rate sensor: the maturity's other sensors, the loans that follow it and
 * the ECB's rate, by the integration's registry entries and attributes rather than by entity ids, which a user can change
 * and which follow Home Assistant's language.
 */
import type { HassEntity, HomeAssistant } from "./hass";

export const PLATFORM = "euribor_rates";

export interface Loan {
    entity: string;
    name: string;
    rate?: number;
    margin: number;
    maturity: string;
    /** The reset that locked the current rate, which tells when the lock periods change. */
    reset?: string;
    pending: boolean;
    locked?: number;
    rateToday?: number;
    change?: number;
    nextReset?: string;
}

export interface Sources {
    rate: HassEntity;
    maturity: string;
    history?: string;
    published?: HassEntity;
    loans: Loan[];
    ecbRate?: HassEntity;
    ecbHistory?: string;
}

/** The maturities' rate sensors, which are what the card is set to. */
export function rateSensors(hass: HomeAssistant): string[] {
    return Object.values(hass.states)
        .filter(
            (state): state is HassEntity => !!state && platformOf(hass, state.entity_id) === PLATFORM && "latest_rate" in state.attributes,
        )
        .map((state) => state.entity_id)
        .sort();
}

export function sources(hass: HomeAssistant, entity: string): Sources | undefined {
    const rate = hass.states[entity];
    const maturity = rate?.attributes.maturity;
    if (!rate || typeof maturity !== "string") {
        return undefined;
    }
    const siblings = (id: string): Record<string, string> => {
        const device = hass.entities?.[id]?.device_id;
        const found: Record<string, string> = {};
        for (const entry of Object.values(hass.entities ?? {})) {
            if (entry && device && entry.device_id === device && entry.platform === PLATFORM) {
                found[entry.translation_key ?? ""] = entry.entity_id;
            }
        }
        return found;
    };
    const own = siblings(entity);
    const ecbRate = Object.values(hass.states).find(
        (state) => !!state && platformOf(hass, state.entity_id) === PLATFORM && "effective_date" in state.attributes,
    );
    return {
        rate,
        maturity,
        history: own.history,
        published: own.published ? hass.states[own.published] : undefined,
        loans: loans(hass, maturity, siblings),
        ecbRate,
        ecbHistory: ecbRate ? siblings(ecbRate.entity_id).history : undefined,
    };
}

function loans(hass: HomeAssistant, maturity: string, siblings: (id: string) => Record<string, string>): Loan[] {
    const result: Loan[] = [];
    for (const state of Object.values(hass.states)) {
        if (
            !state ||
            platformOf(hass, state.entity_id) !== PLATFORM ||
            !("margin" in state.attributes) ||
            state.attributes.maturity !== maturity
        ) {
            continue;
        }
        const own = siblings(state.entity_id);
        const reference = own.reference_rate ? hass.states[own.reference_rate] : undefined;
        const attributes = state.attributes;
        result.push({
            entity: state.entity_id,
            name: hass.formatEntityName?.(state, [{ type: "device" }]) || String(attributes.friendly_name ?? state.entity_id),
            rate: number(state.state),
            margin: Number(attributes.margin),
            maturity,
            reset: text(attributes.reset_date),
            pending: attributes.pending === true,
            locked: number(reference?.state),
            rateToday: number(own.rate_today ? hass.states[own.rate_today]?.state : undefined),
            change: number(own.change ? hass.states[own.change]?.state : undefined),
            nextReset: text(own.next_reset ? hass.states[own.next_reset]?.state : undefined),
        });
    }
    return result.sort((a, b) => a.name.localeCompare(b.name));
}

function platformOf(hass: HomeAssistant, entity: string): string | undefined {
    return hass.entities?.[entity]?.platform;
}

function number(value: string | undefined): number | undefined {
    const parsed = value === undefined ? NaN : Number(value);
    return Number.isFinite(parsed) && value !== "" ? parsed : undefined;
}

function text(value: unknown): string | undefined {
    return typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value) ? value : undefined;
}
