import { ModulePage } from "@/components/layout/module-page";
import { findPlatformModule } from "@/data/platform";

export default function HrPage() {
  return <ModulePage module={findPlatformModule("hr")!} />;
}
