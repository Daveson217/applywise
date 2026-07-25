export const STATUS_OPTIONS = [
  { value: "saved", label: "Saved" },
  { value: "applied", label: "Applied" },
  { value: "oa_assessment", label: "OA/Assessment" },
  { value: "phone_screen", label: "Phone Screen" },
  { value: "interview", label: "Interview" },
  { value: "final_round", label: "Final Round" },
  { value: "offer_received", label: "Offer Received" },
  { value: "accepted", label: "Accepted" },
  { value: "rejected", label: "Rejected" },
  { value: "withdrawn", label: "Withdrawn" },
  { value: "ghosted", label: "Ghosted" },
] as const;

export const STATUS_COLORS: Record<string, string> = {
  saved: "bg-status-saved",
  applied: "bg-status-applied",
  oa_assessment: "bg-status-oa",
  phone_screen: "bg-status-phone",
  interview: "bg-status-interview",
  final_round: "bg-status-final",
  offer_received: "bg-status-offer",
  accepted: "bg-status-accepted",
  rejected: "bg-status-rejected",
  withdrawn: "bg-status-withdrawn",
  ghosted: "bg-status-ghosted",
};

export const STATUS_LABELS: Record<string, string> = Object.fromEntries(
  STATUS_OPTIONS.map((s) => [s.value, s.label])
);

export const JOB_TYPE_OPTIONS = [
  { value: "internship", label: "Internship" },
  { value: "coop", label: "Co-op" },
  { value: "fulltime", label: "Full-time" },
  { value: "parttime", label: "Part-time" },
  { value: "contract", label: "Contract" },
] as const;

export const SOURCE_OPTIONS = [
  { value: "linkedin", label: "LinkedIn" },
  { value: "handshake", label: "Handshake" },
  { value: "indeed", label: "Indeed" },
  { value: "direct", label: "Direct" },
  { value: "referral", label: "Referral" },
  { value: "career_fair", label: "Career Fair" },
  { value: "other", label: "Other" },
] as const;

export const PRIORITY_OPTIONS = [
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
] as const;

export const STATUS_FILTER_GROUPS = [
  { label: "All", statuses: [] },
  { label: "Saved", statuses: ["saved"] },
  { label: "Applied", statuses: ["applied"] },
  {
    label: "Interviewing",
    statuses: ["oa_assessment", "phone_screen", "interview", "final_round"],
  },
  { label: "Offers", statuses: ["offer_received", "accepted"] },
  { label: "Closed", statuses: ["rejected", "withdrawn", "ghosted"] },
] as const;
