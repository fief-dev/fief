import React from 'react';

import { useCountriesCache } from '../../hooks/country';

interface CountryInputProps extends React.DetailedHTMLProps<React.SelectHTMLAttributes<HTMLSelectElement>, HTMLSelectElement> {
  allowEmpty?: boolean;
}

const CountryInput = React.forwardRef<any, CountryInputProps>(({ allowEmpty, ...props }, ref) => {
  const [countries, loading] = useCountriesCache();

  return (
    <>
      {!loading &&
        <select
          ref={ref}
          {...props}
        >
          {allowEmpty && <option value=""></option>}
          {countries.map((country) =>
            <option key={country.alpha_2} value={country.alpha_2}>{country.name}</option>
          )}
        </select>
      }
    </>
  );
});

CountryInput.defaultProps = {
  allowEmpty: false,
}

export default CountryInput;
