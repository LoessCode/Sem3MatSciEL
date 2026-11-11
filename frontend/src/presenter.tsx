import { createContext, useContext, type ReactNode } from "react";

export const PresenterContext = createContext(false);

/** One-line plain-language caption, shown only when Presenter mode is on. */
export function Caption({ children }: { children: ReactNode }) {
  const on = useContext(PresenterContext);
  if (!on) return null;
  return <p className="caption" role="note">{children}</p>;
}
