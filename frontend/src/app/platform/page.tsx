import { ModulePage } from "@/components/layout/module-page";
import { findPlatformModule } from "@/data/platform";

export default function PlatformPage() {
  return <ModulePage module={findPlatformModule("core")!} />;
}
