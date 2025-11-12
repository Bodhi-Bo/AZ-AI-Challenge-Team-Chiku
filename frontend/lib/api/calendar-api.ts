// lib/api/calendar-api.ts
import { CalendarEventsResponse, CalendarEvent } from '@/types';
import { format, subDays, addDays } from 'date-fns';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function fetchEventsRange(
  userId: string,
  centerDate: Date
): Promise<CalendarEvent[]> {
  // Calculate 3 days back and 3 days forward
  const startDate = subDays(centerDate, 3);
  const endDate = addDays(centerDate, 3);

  const start = format(startDate, 'yyyy-MM-dd');
  const end = format(endDate, 'yyyy-MM-dd');

  const response = await fetch(
    `${API_URL}/events/${userId}/range?start_date=${start}&end_date=${end}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch events: ${response.status}`);
  }

  const data: CalendarEventsResponse = await response.json();
  return data.events;
}
