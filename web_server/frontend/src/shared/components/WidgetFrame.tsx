import React from "react";

type WidgetFrameProps = {
  title: string;
  children: React.ReactNode;
};

export function WidgetFrame({ title, children }: WidgetFrameProps) {
  return (
    <section className="card">
      <h2 className="card__title">{title}</h2>
      {children}
    </section>
  );
}
