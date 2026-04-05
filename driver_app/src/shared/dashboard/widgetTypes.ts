import type { ReactNode } from "react";

export type WidgetDefinition = {
  id: string;
  title: string;
  render: () => ReactNode;
};
