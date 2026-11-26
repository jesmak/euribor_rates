import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { LANGUAGE_CODES, translate } from "../src/localize/localize";

// The tests run from the repository root.
const FOLDER = join(process.cwd(), "src", "localize", "languages");

function keys(table: Record<string, unknown>, prefix = ""): string[] {
    return Object.entries(table).flatMap(([key, value]) =>
        value !== null && typeof value === "object" ? keys(value as Record<string, unknown>, `${prefix}${key}.`) : [`${prefix}${key}`],
    );
}

function language(code: string): Record<string, unknown> {
    return JSON.parse(readFileSync(join(FOLDER, `${code}.json`), "utf8"));
}

describe("languages", () => {
    it("are every JSON file in the languages folder", () => {
        const files = readdirSync(FOLDER)
            .filter((file) => file.endsWith(".json"))
            .map((file) => file.replace(/\.json$/, "").toLowerCase())
            .sort();
        expect(LANGUAGE_CODES).toEqual(files);
        expect(LANGUAGE_CODES).toContain("en");
    });

    it.each(LANGUAGE_CODES.filter((code) => code !== "en"))("%s has the same keys as English", (code) => {
        expect(keys(language(code)).sort()).toEqual(keys(language("en")).sort());
    });

    it("fall back to English for a text a language lacks, and to the key for one nobody has", () => {
        expect(translate("fi", "card.now")).toBe("nyt");
        expect(translate("xx", "card.now")).toBe(translate("en", "card.now"));
        expect(translate("fi-FI", "card.now")).toBe("nyt");
        expect(translate("fi_FI", "card.now")).toBe("nyt");
        expect(translate("xx-YY", "card.now")).toBe(translate("en", "card.now"));
        expect(translate("fi", "no.such.key")).toBe("no.such.key");
    });
});
