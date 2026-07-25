import { ContactList } from "@/features/networking/components/contact-list";

export function NetworkingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold">
          Networking
        </h1>
        <p className="text-muted-foreground">
          Track recruiters, referrals, and networking contacts.
        </p>
      </div>

      <ContactList />
    </div>
  );
}
