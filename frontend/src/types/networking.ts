export interface Contact {
  id: number;
  name: string;
  company: string;
  role: string;
  email: string;
  linkedin_url: string;
  relationship_type: string;
  notes: string;
  interactions_count: number;
  last_interaction_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface Interaction {
  id: number;
  type: string;
  date: string;
  notes: string;
  linked_application: number | null;
  created_at: string;
}

export interface CreateContactData {
  name: string;
  company?: string;
  role?: string;
  email?: string;
  linkedin_url?: string;
  relationship_type?: string;
  notes?: string;
}

export interface CreateInteractionData {
  type: string;
  date: string;
  notes?: string;
  linked_application?: number | null;
}
