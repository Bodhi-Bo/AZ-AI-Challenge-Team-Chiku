// lib/api/reminder-api.ts
import { RemindersResponse, Reminder } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL;

export async function fetchUpcomingReminders(
  userId: string,
  hoursAhead: number = 24
): Promise<Reminder[]> {
  const response = await fetch(
    `${API_URL}/reminders/${userId}/upcoming?hours_ahead=${hoursAhead}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch reminders: ${response.status}`);
  }

  const data: RemindersResponse = await response.json();
  return data.reminders;
}
