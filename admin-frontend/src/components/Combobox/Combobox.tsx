import { useState, Fragment, useCallback, useEffect } from 'react';
import { Combobox as BaseCombobox } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/20/solid';

export interface ComboboxOption {
  value: string;
  label: string;
}

interface ComboboxProps {
  initialOptions?: ComboboxOption[];
  noOptionLabel?: string;
  onSearch?: (query: string) => Promise<ComboboxOption[]>;
  value?: string;
  onChange?: (value: string) => void;
}

const Combobox: React.FunctionComponent<React.PropsWithChildren<ComboboxProps>> = ({ initialOptions, noOptionLabel, onSearch, value, onChange: _onChange }) => {
  const [selected, setSelected] = useState<ComboboxOption | undefined>(undefined);
  const [options, setOptions] = useState<ComboboxOption[]>([]);
  const [query, setQuery] = useState('');

  const onChange = useCallback((option: ComboboxOption) => {
    setSelected(option);
    if (_onChange) {
      _onChange(option.value);
    }
  }, [_onChange]);

  useEffect(() => {
    if (value && selected?.value !== value) {
      const option = options.find((option) => option.value === value);
      setSelected(option);
    }
  }, [value, selected, options]);

  useEffect(() => {
    if (initialOptions && initialOptions.length > 0) {
      setOptions(initialOptions);
    }
  }, [initialOptions]);

  useEffect(() => {
    if (query && onSearch) {
      onSearch(query).then((options) => setOptions(options));
    }
  }, [query, onSearch])

  return (
    <BaseCombobox value={selected} onChange={onChange}>
      <div className="relative">
        <BaseCombobox.Input<"input", ComboboxOption>
          onChange={(event) => setQuery(event.target.value)}
          displayValue={(option) => option?.label}
          className="form-input w-full"
        />
        <BaseCombobox.Button className="ml-3 absolute inset-y-0 right-0 flex items-center pr-2">
          <ChevronDownIcon width={16} height={16} className="fill-slate-400" />
        </BaseCombobox.Button>
      </div>
      <BaseCombobox.Options
        className="border border-slate-200 p-2 rounded shadow-lg overflow-hidden mt-1 text-sm"
      >
        {options.length === 0 &&
          <span className="py-1 px-3">{noOptionLabel}</span>
        }
        {options.map((option) => (
          <BaseCombobox.Option
            key={option.value} value={option} as={Fragment}>
            {({ selected, active }) => (
              <li
                className={
                  `flex items-center py-1 px-3
                  ${selected ? 'text-primary-500' : 'text-slate-600'}
                  ${active ? 'bg-slate-100' : ''}
                `}
              >
                {option.label}
              </li>
            )}
          </BaseCombobox.Option>
        ))}
      </BaseCombobox.Options>
    </BaseCombobox>
  )
};

export default Combobox;
