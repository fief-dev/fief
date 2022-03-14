import { useMemo } from 'react';

export const useFormattedDateTime = (datetime: string | Date, displayTime: boolean): string => {
  const formatted = useMemo(() => {
    return new Date(datetime).toLocaleString(
      undefined,
      {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        ...displayTime ? { hour: '2-digit', minute: '2-digit' } : {},
      },
    );
  }, [datetime, displayTime]);

  return formatted;
};
