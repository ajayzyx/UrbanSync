import clsx from "clsx";
import type { ReactNode } from "react";

export function Panel({ title, eyebrow, actions, children, className, bodyClassName }: {
  title?: ReactNode;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section className={clsx("rounded-xl border border-line bg-panel shadow-[0_1px_2px_rgba(23,32,42,0.04)]", className)}>
      {(title || eyebrow || actions) && (
        <header className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
          <div className="min-w-0">
            {eyebrow && <div className="micro mb-0.5">{eyebrow}</div>}
            {title && <h2 className="font-display truncate text-[15px] font-medium text-text">{title}</h2>}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={clsx("p-4", bodyClassName)}>{children}</div>
    </section>
  );
}

export function Button({ children, variant = "ghost", className, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "danger";
}) {
  return (
    <button
      {...props}
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-accent text-white hover:bg-[#0d9488]",
        variant === "ghost" && "border border-line-2 bg-panel text-text hover:border-accent/60 hover:text-accent",
        variant === "danger" && "border border-bad/40 bg-bad/[0.06] text-[#991b1b] hover:bg-bad/10",
        className,
      )}
    >
      {children}
    </button>
  );
}
