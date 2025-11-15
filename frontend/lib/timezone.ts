/**
 * Timezone utility for converting dates to MST (Mountain Standard Time)
 * MST is UTC-7
 */

const MST_OFFSET = -7; // MST is UTC-7

/**
 * Get current time in MST timezone
 */
export function getCurrentMSTTime(): Date {
  return convertToMST(new Date());
}

/**
 * Convert any date to MST timezone
 */
export function convertToMST(date: Date): Date {
  // Get UTC time
  const utcTime = date.getTime() + date.getTimezoneOffset() * 60000;

  // Convert to MST (UTC-7)
  const mstTime = new Date(utcTime + MST_OFFSET * 3600000);

  return mstTime;
}

/**
 * Format date to MST timezone string
 */
export function formatMSTDate(date: Date, formatStr?: string): string {
  const mstDate = convertToMST(date);

  if (formatStr) {
    // Use the format string with the MST date
    return mstDate.toLocaleString('en-US', { timeZone: 'America/Denver' });
  }

  return mstDate.toLocaleString('en-US', { timeZone: 'America/Denver' });
}

/**
 * Create a date in MST timezone from components
 */
export function createMSTDate(
  year: number,
  month: number,
  day: number,
  hour: number = 0,
  minute: number = 0,
  second: number = 0
): Date {
  // Create date in MST
  const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}T${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:${String(second).padStart(2, '0')}`;
  const utcDate = new Date(dateStr + 'Z'); // Parse as UTC

  // Adjust from UTC to MST
  return new Date(utcDate.getTime() - MST_OFFSET * 3600000);
}

/**
 * Parse ISO string and convert to MST
 */
export function parseISOToMST(isoString: string): Date {
  return convertToMST(new Date(isoString));
}

/**
 * Get MST offset string (for display)
 */
export function getMSTOffsetString(): string {
  return 'MST (UTC-7)';
}
