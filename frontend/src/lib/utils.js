import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Compose class name inputs and merge Tailwind CSS classes, resolving conflicting utilities.
 * @param {...any} inputs - Class name values accepted by `clsx` (strings, arrays, objects, etc.).
 * @returns {string} The resulting merged class string with Tailwind conflicts resolved.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}