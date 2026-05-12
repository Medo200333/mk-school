import { ModulePage } from "@/components/layout/module-page";
import { findPlatformModule } from "@/data/platform";

export default function OperationsPage() {
  return <ModulePage module={findPlatformModule("operations")!} />;
}
