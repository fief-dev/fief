import React from 'react';

import { useTimezonesCache } from '../../hooks/timezone';

interface TimezoneInputProps extends React.DetailedHTMLProps<React.SelectHTMLAttributes<HTMLSelectElement>, HTMLSelectElement> {
  allowEmpty?: boolean;
}

const TimezoneInput = React.forwardRef<any, TimezoneInputProps>(({ allowEmpty, ...props }, ref) => {
  const [timezones, loading] = useTimezonesCache();

  return (
    <>
      {!loading &&
        <select
          ref={ref}
          {...props}
        >
          {allowEmpty && <option value=""></option>}
          {timezones.map((timezone) =>
            <option key={timezone} value={timezone}>{timezone}</option>
          )}
        </select>
      }
    </>
  );
});

TimezoneInput.defaultProps = {
  allowEmpty: false,
}

export default TimezoneInput;
