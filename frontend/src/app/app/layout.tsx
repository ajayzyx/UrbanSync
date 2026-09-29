import { Shell } from "@/components/ui/Shell";

export default function WorkspaceLayout({ children }: LayoutProps<"/app">) {
  return <Shell>{children}</Shell>;
}
