import flatpickr from 'flatpickr';
import { RefObject, useEffect, useRef } from 'react';

export const useDatePicker = (
  value: string | null | undefined,
  time: boolean,
  onClose?: (value: string | null) => void,
): RefObject<any> => {
  const element = useRef<HTMLElement>(null);
  const flatpickrInstance = useRef<flatpickr.Instance>();

  useEffect(() => {
    if (element.current) {
      const onDateChange = (dates: Date[]) => {
        if (dates.length > 0) {
          const date = dates[0];
          if (onClose) {
            let isoString = date.toISOString();
            if (!time) {
              isoString = isoString.split('T')[0];
            }
            onClose(isoString);
          }
        } else {
          if (onClose) {
            onClose(null);
          }
        }
      };

      const instance = flatpickr(
        element.current,
        {
          static: true,
          enableTime: time,
          altInput: true,
          altFormat: time ? 'F j, Y H:i' : 'F j, Y',
          time_24hr: true,
          onClose: onDateChange,
          ...value ? { defaultDate: new Date(value) } : {},
        },
      );
      flatpickrInstance.current = instance;
    }

    return () => flatpickrInstance.current?.destroy();
  }, [element, value, time, onClose]);

  return element;
};
