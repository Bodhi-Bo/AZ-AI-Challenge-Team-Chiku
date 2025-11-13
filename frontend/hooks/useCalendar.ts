// hooks/useCalendar.ts
'use client';

import { useEffect } from 'react';
import { useCalendarStore } from '@/lib/stores/calendarStore';
import { fetchEventsRange } from '@/lib/api/calendar-api';
import { format, subDays, addDays } from 'date-fns';

export function useCalendar() {
  const calendarStore = useCalendarStore();
  const userId = process.env.NEXT_PUBLIC_USER_ID || 'user_123';

  const loadEvents = async (date: Date) => {
    calendarStore.setLoading(true);

    try {
      const events = await fetchEventsRange(userId, date);
      calendarStore.setEvents(events);

      // Track loaded range
      const start = format(subDays(date, 3), 'yyyy-MM-dd');
      const end = format(addDays(date, 3), 'yyyy-MM-dd');
      calendarStore.setDateRange(start, end);
    } catch (error) {
      console.error('Failed to load calendar:', error);
    } finally {
      calendarStore.setLoading(false);
    }
  };

  // Load events on mount
  useEffect(() => {
    loadEvents(calendarStore.selectedDate);
  }, []);

  return { loadEvents };
}
