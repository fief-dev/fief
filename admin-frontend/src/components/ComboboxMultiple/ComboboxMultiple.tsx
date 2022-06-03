import * as R from 'ramda';
import { useState, Fragment, useCallback, useEffect } from 'react';
import { Combobox as BaseCombobox } from '@headlessui/react';
import { ChevronDownIcon, XIcon } from '@heroicons/react/solid';

export interface ComboboxMultipleOption {
  value: string;
  label: string;
}

interface ComboboxMultipleProps {
  initialOptions?: ComboboxMultipleOption[];
  noOptionLabel?: string;
  onSearch?: (query: string) => Promise<ComboboxMultipleOption[]>;
  value?: string[];
  onChange?: (value: string[]) => void;
}

const ComboboxMultiple: React.FunctionComponent<React.PropsWithChildren<ComboboxMultipleProps>> = ({ initialOptions, noOptionLabel, onSearch, value, onChange: _onChange }) => {
  const [selected, setSelected] = useState<ComboboxMultipleOption[]>([]);
  const [options, setOptions] = useState<ComboboxMultipleOption[]>(initialOptions || []);
  const [query, setQuery] = useState('');

  const onChange = useCallback((options: ComboboxMultipleOption[]) => {
    setSelected(options);
    if (_onChange) {
      _onChange(options.map(({ value }) => value));
    }
  }, [_onChange]);

  useEffect(() => {
    if (value) {
      if (R.equals(selected.map(({ value }) => value), value)) {
        return;
      }

      const updatedSelected = value.reduce<ComboboxMultipleOption[]>(
        (selected, singleValue) => {
          const option = options.find((option) => option.value === singleValue);
          if (option) {
            return [
              ...selected,
              option,
            ];
          }
          return selected;
        },
        [],
      );
      setSelected(updatedSelected);
    }
  }, [value, selected, options]);

  useEffect(() => {
    if (initialOptions && initialOptions.length > 0) {
      setOptions(initialOptions);
    }
  }, [initialOptions]);

  useEffect(() => {
    if (query && onSearch) {
      onSearch(query).then((options) => {
        setOptions(R.uniqBy(R.prop('value'), [...selected, ...options]));
      });
    }
  }, [query, onSearch, selected]);

  return (
    <BaseCombobox value={selected} onChange={onChange} multiple>
      <div className="relative">
        <span className="inline-block w-full">
          <div className="relative w-full form-input focus-within:border-primary-300">
            <span className="block flex flex-wrap gap-2">
              {selected.map((option) => (
                <span
                  key={option.value}
                  className="text-xs inline-flex items-center font-medium bg-slate-100 text-slate-500 rounded-full px-2.5 py-1"
                >
                  <span>{option.label}</span>
                  <XIcon
                    width={16}
                    height={16}
                    onClick={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      onChange(selected.filter(({ value }) => value !== option.value));
                    }}
                  />
                </span>
              ))}
            </span>
            <BaseCombobox.Input<"input", ComboboxMultipleOption>
              onChange={(event) => setQuery(event.target.value)}
              displayValue={() => query}
              className="border-none p-0 focus:ring-0 w-full"
            />
            <BaseCombobox.Button className="ml-3 absolute inset-y-0 right-0 flex items-center pr-2">
              <ChevronDownIcon width={16} height={16} className="fill-slate-400" />
            </BaseCombobox.Button>
          </div>
        </span>
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

export default ComboboxMultiple;
