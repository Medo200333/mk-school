import { ModulePage } from "@/components/layout/module-page";
import { findPlatformModule } from "@/data/platform";

export default function SchoolPage() {
  return <ModulePage module={findPlatformModule("school")!} />;
}
