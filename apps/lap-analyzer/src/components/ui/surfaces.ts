// Surface recipes copied from the save viewer (components/ui/surfaces.ts) so
// the selection UI looks the same. Tokens live in index.css.

export const cardSurface = "rounded-2xl bg-tone-900 ring-1 ring-tone-800";
export const insetTileClass = "rounded-xl bg-tone-800/40 ring-1 ring-tone-800";
export const floatingSurface = "bg-tone-900 ring-1 ring-tone-700 shadow-2xl shadow-tone-1000/40";
export const menuSurfaceClass = `rounded-xl p-1.5 ${floatingSurface}`;

// A row in a list nothing manages: lights on hover and focus. A picked row
// sets aria-pressed.
export const listItemClass =
  "flex w-full items-center gap-x-2 rounded-lg px-2.5 py-1.5 text-left outline-none transition-colors select-none hover:bg-tone-800 focus-visible:bg-tone-800 data-disabled:pointer-events-none data-disabled:opacity-50 aria-pressed:bg-tone-800 aria-pressed:text-tone-100 aria-pressed:ring-1 aria-pressed:ring-inset aria-pressed:ring-tone-0/[0.08]";
