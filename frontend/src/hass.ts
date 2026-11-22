/** The little of Home Assistant a card needs, so the unmaintained custom-card-helpers isn't a dependency. */

export interface HassEntity {
    entity_id: string;
    state: string;
    last_changed: string;
    attributes: Record<string, unknown>;
}

/** An entity's entry in the frontend's registry, which leaves out a disabled one. */
export interface EntityRegistryEntry {
    entity_id: string;
    device_id?: string | null;
    platform: string;
    translation_key?: string | null;
}

/** One part of an entity's name, as `formatEntityName` puts them together. */
export interface NamePart {
    type: "entity" | "device" | "area" | "floor";
}

export interface HomeAssistant {
    states: Record<string, HassEntity | undefined>;
    entities?: Record<string, EntityRegistryEntry | undefined>;
    callWS?<T>(message: Record<string, unknown>): Promise<T>;
    formatEntityName?(state: HassEntity, parts: NamePart[]): string;
    language?: string;
    locale?: { language?: string };
    config?: { time_zone?: string };
}

export interface LovelaceCardConfig {
    type: string;
    [key: string]: unknown;
}
