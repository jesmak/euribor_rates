import { expect, test, vi } from "vitest";

// Another copy of the card, such as one copied by hand, may be loaded first.
test("a copy of the card loaded earlier stays the card and its editor, and the picker lists it once", async () => {
    class Earlier extends HTMLElement {}
    class EarlierEditor extends HTMLElement {}
    customElements.define("euribor-card", Earlier);
    customElements.define("euribor-card-editor", EarlierEditor);
    const registry = window as unknown as { customCards?: unknown[] };
    registry.customCards = [{ type: "euribor-card" }];
    const info = vi.spyOn(console, "info").mockImplementation(() => undefined);

    await import("../src/euribor-card");

    expect(customElements.get("euribor-card")).toBe(Earlier);
    expect(customElements.get("euribor-card-editor")).toBe(EarlierEditor);
    expect(registry.customCards).toHaveLength(1);
    expect(info).not.toHaveBeenCalled();
});
