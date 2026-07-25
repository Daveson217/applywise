import { CVList } from "@/features/cv/components/cv-list";

export function CVPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold">
          CV Manager
        </h1>
        <p className="text-muted-foreground">
          Upload and manage your resume versions.
        </p>
      </div>

      <CVList />
    </div>
  );
}
